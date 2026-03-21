#!/usr/bin/python
# -*- coding:utf-8 -*-
from bmp280 import BMP280
import time
import datetime
import math
import sys
import os
import subprocess
import signal
from threading import Timer
from gpiozero import Button
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib_screen')




if os.path.exists(libdir):
    sys.path.append(libdir)

import logging    
import traceback
from waveshare_OLED import OLED_1in32
from PIL import Image,ImageDraw,ImageFont
logging.basicConfig(level=logging.WARNING)
from smbus2 import SMBus
import serial
import pynmea2
import threading


class KalmanFilter1D:
    """Fuses GPS speed (update) and IMU acceleration (predict) via a 1-D Kalman filter."""

    def __init__(self, process_noise=0.05, measurement_noise=0.0337):
        self.q = process_noise       # IMU model uncertainty  (km/h)^2 / s
        self.r = measurement_noise   # GPS measurement noise  (km/h)^2 
        self.x = 0.0                 # estimated speed in km/h
        self.p = 1.0                 # error covariance

    def predict(self, accel_kmh_s, dt):
        """Propagate state forward using IMU-derived acceleration."""
        self.x = max(0.0, self.x + accel_kmh_s * dt)
        self.p += self.q * dt
        return self.x

    def update(self, gps_speed_kmh):
        """Correct state using a GPS speed measurement."""
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (gps_speed_kmh - self.x)
        self.p = (1.0 - k) * self.p
        return self.x

# --- Camera / button ---
output_dir = "/home/missmaxine/snowy_media"
os.makedirs(output_dir, exist_ok=True)

click_timer = None
double_click_time = 0.3

def capture_image(out_dir):
    global is_capturing
    is_capturing = True
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    filepath = os.path.join(out_dir, filename)
    p = subprocess.run(["rpicam-still", "-o", filepath])
    is_capturing = False
    if p.returncode != 0 or not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        raise RuntimeError("Camera capture failed or produced no file.")
    print(f"Image saved: {filepath}")

video_process = None
is_recording = False
is_capturing = False

def start_recording(out_dir):
    global video_process, is_recording
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"
    filepath = os.path.join(out_dir, filename)
    video_process = subprocess.Popen(["rpicam-vid", "-t", "0",
                    "--codec", "libav", "--libav-format", "mp4", "-o", filepath])
    is_recording = True
    print(f"Recording started: {filepath}")

def stop_recording():
    global video_process, is_recording
    if video_process is not None:
        video_process.send_signal(signal.SIGINT)
        video_process.wait()
        video_process = None
    is_recording = False
    print("Recording stopped.")

def on_press():
    global click_timer
    if click_timer is not None and click_timer.is_alive():
        click_timer.cancel()
        click_timer = None
        if is_recording:
            click_timer = Timer(double_click_time, stop_recording)
        else:
            click_timer = Timer(double_click_time, start_recording, args=(output_dir,))
        click_timer.start()
    else:
        click_timer = Timer(double_click_time, capture_image, args=(output_dir,))
        click_timer.start()

button = Button(16, bounce_time=0.05)
button.when_pressed = on_press

# --- Hardware setup ---
MPU6050_ADDR = 0x68
bus = SMBus(1)
# Wake up the MPU6050
bus.write_byte_data(MPU6050_ADDR, 0x6B, 0)

# --- BN220 GPS serial reader (background thread) ---
GPS_SERIAL_PORT = "/dev/ttyAMA0"
GPS_BAUD_RATE   = 9600
_gps_lock = threading.Lock()
_gps_data = {"gps_qual": 0, "speed_over_ground": None}

def _gps_reader_thread():
    try:
        with serial.Serial(GPS_SERIAL_PORT, GPS_BAUD_RATE, timeout=1) as ser:
            while True:
                try:
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("ascii", errors="replace").strip()
                    if not line.startswith("$"):
                        continue
                    msg = pynmea2.parse(line)
                    if isinstance(msg, pynmea2.RMC):
                        with _gps_lock:
                            if msg.status == "A" and msg.spd_over_grnd is not None:
                                _gps_data["gps_qual"] = 1
                                _gps_data["speed_over_ground"] = float(msg.spd_over_grnd)
                            else:
                                _gps_data["gps_qual"] = 0
                                _gps_data["speed_over_ground"] = None
                    elif isinstance(msg, pynmea2.GGA) and msg.gps_qual is not None:
                        with _gps_lock:
                            _gps_data["gps_qual"] = int(msg.gps_qual)
                except (pynmea2.ParseError, UnicodeDecodeError):
                    continue
    except Exception:
        pass

def get_gps_data():
    with _gps_lock:
        return dict(_gps_data)

# --- IMU (MPU6050) helpers ---
ACCEL_XOUT_H      = 0x3B
ACCEL_SENSITIVITY = 16384.0
GRAVITY           = 9.81

def _read_raw_accel_x():
    raw = bus.read_i2c_block_data(MPU6050_ADDR, ACCEL_XOUT_H, 2)
    val = (raw[0] << 8) | raw[1]
    return val - 65536 if val > 32768 else val

def calibrate_imu(samples=100):
    total = 0
    for _ in range(samples):
        total += _read_raw_accel_x()
        time.sleep(0.002)
    return total / samples

bmp = BMP280(i2c_dev=bus, i2c_addr=0x76)


try:
    # time.sleep(60)
    disp = OLED_1in32.OLED_1in32()

    gps_thread = threading.Thread(target=_gps_reader_thread, daemon=True)
    gps_thread.start()

    print("Calibrating IMU... keep still.")
    imu_offset = calibrate_imu()
    print(f"IMU calibrated. Offset: {imu_offset:.2f}")

    last_time = time.time()
    last_display_time = time.time()

    print("speedometer booting")

    logging.info("\r 1.32inch OLED ")

    font = ImageFont.truetype('Font.ttc',15)
    font_large = ImageFont.truetype('Font.ttc', 15)  # speed
    font_small = ImageFont.truetype('Font.ttc', 10)  # temp & altitude

    disp.Init()
    time.sleep(0.2)
    disp.clear()
    time.sleep(0.2)
    disp.Init()
    time.sleep(0.2)
    disp.clear()

    kf = KalmanFilter1D()
    fused_speed_kmh = 0.0

    # clear image buffer
    image1 = Image.new('L', (disp.height, disp.width), 0)
    disp.ShowImage(disp.getbuffer(image1))
    time.sleep(0.2)
    
    log_file = open("speed_log.csv", "a")
    last_log_time = time.time()
    while 1:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
    
        temp_c = bmp.get_temperature()
        # temp_c = 22
        temp_str = f"{temp_c:.2f} °C"
        pressure_hpa = bmp.get_pressure()
        qnh = 1015
        pressure_pa = pressure_hpa*100.0
        altitude_m = (((qnh/pressure_hpa)**(1.0/5.257)-1.0)*(temp_c+273))/0.0065
        alt_str = f"{altitude_m:.2f} m"
        
  

        # IMU predict: propagate speed estimate using acceleration
        raw_val = _read_raw_accel_x()
        accel_ms2 = ((raw_val - imu_offset) / ACCEL_SENSITIVITY) * GRAVITY
        if abs(accel_ms2) < 0.15:   # zero-velocity threshold to suppress drift
            accel_ms2 = 0.0
        fused_speed_kmh = kf.predict(accel_ms2 * 3.6, dt)

        # GPS update: correct estimate when a valid fix is available
        data = get_gps_data()
        gpsqual = data.get('gps_qual', 0)
        speed = data.get('speed_over_ground', 0.0)
        if speed is None or speed == 0.0:
            speed_str = "0.0 km/h"
        else:
            speed_kmh = speed * 1.852  # convert knots to km/h
            fused_speed_kmh = kf.update(speed_kmh)
            speed_str = f"{fused_speed_kmh:.2f} km/h"

        image1 = Image.new('L', (disp.height, disp.width), 0)
        draw = ImageDraw.Draw(image1)
        
        # 4. Draw to Canvas
        draw.text((55, 40), alt_str, font=font_small, fill=15)
        draw.text((5,40), temp_str, font=font_small, fill=15)
        draw.text((20, disp.width//2 + 20), speed_str, font=font_large, fill=15)

        if is_capturing:
            if int(time.time() * 4) % 2 == 0:
                draw.ellipse([(85, 102), (95, 111)], fill=15)
        elif is_recording:
            draw.ellipse([(85, 102), (95, 111)], fill=15)

        image1 = image1.rotate(270)
        image1 = image1.transpose(Image.FLIP_TOP_BOTTOM)
        disp.ShowImage(disp.getbuffer(image1))
        

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    disp.clear()
    
    disp.module_exit()
    exit()

