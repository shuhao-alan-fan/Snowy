#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import math
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib_screen')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging    
import traceback
from waveshare_OLED import OLED_1in32
from PIL import Image,ImageDraw,ImageFont
logging.basicConfig(level=logging.DEBUG)
from smbus2 import SMBus

#!/usr/bin/env python3


from pa1010d import PA1010D

class KalmanFilter1D:
    def __init__(self, initial_velocity=0.0):
        self.velocity = initial_velocity
        self.P = 1.0 
        self.Q = 0.05  # IMU Variance (Tune this based on resting noise)
        self.R = 0.13  # GPS Variance (Derived from PA1010D 0.1m/s accuracy)

    def predict(self, accel_m_s2, dt):
        # Convert acceleration to km/h change
        delta_v_kmh = (accel_m_s2 * dt) * 3.6
        self.velocity += delta_v_kmh
        self.P += self.Q
        return self.velocity

    def update(self, gps_speed_kmh):
        K = self.P / (self.P + self.R)
        self.velocity = self.velocity + K * (gps_speed_kmh - self.velocity)
        self.P = (1.0 - K) * self.P
        
        # Prevent backward drift when standing still
        if self.velocity < 0.5:
            self.velocity = 0.0
        return self.velocity

MPU6050_ADDR = 0x68
bus = SMBus(1)
# Wake up the MPU6050
bus.write_byte_data(MPU6050_ADDR, 0x6B, 0)



def read_raw_mpu(addr):
    high = bus.read_byte_data(MPU6050_ADDR, addr)
    low = bus.read_byte_data(MPU6050_ADDR, addr+1)
    val = (high << 8) | low
    return val - 65536 if val > 32768 else val

def get_gps_data(gps_sensor):
    result = gps_sensor.update()
    if result:
        return gps_sensor.data
    return None



a = 1
try:
    # time.sleep(60)
    disp = OLED_1in32.OLED_1in32()

    gps = PA1010D()
    gps.send_command('PMTK220,100')

    last_time = time.time()
    last_display_time = time.time()

    print("speedometer booting")

    logging.info("\r 1.32inch OLED ")


    disp.Init()
    time.sleep(0.2)
    disp.clear()
    time.sleep(0.2)
    disp.Init()
    time.sleep(0.2)
    disp.clear()

    kf = KalmanFilter1D()
    pitch = 0.0
    alpha = 0.98
    fused_speed_kmh = 0.0
    
    # clear image buffer
    image1 = Image.new('L', (disp.height, disp.width), 0)
    disp.ShowImage(disp.getbuffer(image1))
    time.sleep(0.2)

    while 1:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time


        acc_y = read_raw_mpu(0x3D) / 16384.0
        acc_z = read_raw_mpu(0x3F) / 16384.0
        gyro_x = read_raw_mpu(0x43) / 131.0

        # Calculate pitch to subtract gravity tilt from forward acceleration
        pitch_acc = math.atan2(acc_y, acc_z) * 180.0 / math.pi
        pitch = alpha * (pitch + gyro_x * dt) + (1.0 - alpha) * pitch_acc
        
        linear_acc_y_g = acc_y - math.sin(pitch * math.pi / 180.0)
        linear_acc_y_m_s2 = linear_acc_y_g * 9.81
        
        # Predict the speed
        fused_speed_kmh = kf.predict(linear_acc_y_m_s2, dt)

        # Create blank image for drawing.
        image1 = Image.new('L', (disp.height, disp.width), 0)
        draw = ImageDraw.Draw(image1)
        font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
        font1 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
        font2 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

        data = get_gps_data(gps)

        if data:
            # Extract speed (Speed Over Ground)
            # print("im here")
            speed = data.get('speed_over_ground', 0.0)
            if speed == None:
                speed_str = f"{0.0}"
            else:
                speed_kmh = speed * 1.852
                fused_speed_kmh = kf.update(speed_kmh)
                speed_str = f"{fused_speed_kmh:.2f}"
            

            # 4. Draw to Canvas
            draw.text((5, 40), "SPEED (km/h)", font=font, fill=15)
            # draw.text((5, 80), str(a), font=font, fill=15)
            draw.text((10, 60), speed_str, font=font, fill=15)

            # draw.text((20, 40), "TIME ()", font=font, fill=15)
            a+=1
        

        # logging.info ("***draw line")
        # draw.line([(0,0),(95,0)], fill = 15)
        # draw.line([(0,0),(0,127)], fill = 15)
        # draw.line([(0,127),(95,127)], fill = 15)
        # draw.line([(95,0),(95,127)], fill = 15)
        # logging.info ("***draw text")
        # draw.text((20,2), 'Hello', font = font1, fill = 13)
  
        image1 = image1.rotate(270)
        disp.ShowImage(disp.getbuffer(image1))
        # time.sleep(3)

        # logging.info ("***draw rectangle")
        # image1 = Image.new('L', (disp.width, disp.height), 0)
        # draw = ImageDraw.Draw(image1)
        # for i in range(0, 16):
        #     draw.rectangle([(8*i, 0), (8*(i+1), 96)], fill = i)
        # disp.ShowImage(disp.getbuffer(image1))
        # time.sleep(3)

        # logging.info ("***draw image")
        # Himage2 = Image.new('L', (disp.width, disp.height), 0)  # 0: clear the frame
        # bmp = Image.open(os.path.join(picdir, '1in32.bmp'))
        # Himage2.paste(bmp, (0,0))
        # disp.ShowImage(disp.getbuffer(Himage2)) 
        # time.sleep(3)    
        # disp.clear()

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    disp.clear()
    disp.module_exit()
    exit()






