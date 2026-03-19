#!/usr/bin/python
# -*- coding:utf-8 -*-
from bmp280 import BMP280
import time
import datetime
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




def get_gps_data(gps_sensor):
    result = gps_sensor.update(wait_for="GGA",timeout=5)
    if result:
        return gps_sensor.data
    return None

# I2C_BUS = 1
# I2C_ADDR = 0x76  # change to 0x77 if your sensor shows 77 in i2cdetect

# bus = SMBus(I2C_BUS)
# bmp = BMP280(i2c_dev=bus, i2c_addr=0x76)


try:
    # time.sleep(60)
    disp = OLED_1in32.OLED_1in32()

    gps = PA1010D()
    gps.send_command('PMTK220,1000')

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

    # kf = KalmanFilter1D()
    # pitch = 0.0
    # alpha = 0.98
    # fused_speed_kmh = 0.0
    
    # clear image buffer
    image1 = Image.new('L', (disp.height, disp.width), 0)
    disp.ShowImage(disp.getbuffer(image1))
    time.sleep(0.2)
    
    # log_file = open("speed_log.csv", "a")
    # last_log_time = time.time()
    while 1:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        

        # acc_y = read_raw_mpu(0x3D) / 16384.0
        # acc_z = read_raw_mpu(0x3F) / 16384.0
        # gyro_x = read_raw_mpu(0x43) / 131.0


        # # bmp
        # temp_c = bmp.get_temperature()
        # # temp_c = 22
        # temp_str = f"{temp_c:.2f} °C"
        # pressure_hpa = bmp.get_pressure()
        # qnh = 1015
        # pressure_pa = pressure_hpa*100.0
        # altitude_m = (((qnh/pressure_hpa)**(1.0/5.257)-1.0)*(temp_c+273))/0.0065
        # alt_str = f"{altitude_m:.2f} m"

        # Calculate pitch to subtract gravity tilt from forward acceleration
        # pitch_acc = math.atan2(acc_y, acc_z) * 180.0 / math.pi
        # pitch = alpha * (pitch + gyro_x * dt) + (1.0 - alpha) * pitch_acc
        
        # linear_acc_y_g = acc_y - math.sin(pitch * math.pi / 180.0)
        # linear_acc_y_m_s2 = linear_acc_y_g * 9.81
        # if(linear_acc_y_m_s2 < 0.3):
        #     linear_acc_y_m_s2 = 0.0
        
        # # Predict the speed
        # fused_speed_kmh = kf.predict(linear_acc_y_m_s2, dt)


        

        # Create blank image for drawing.
        
        
  

        data = get_gps_data(gps)

        if data:
            # Extract speed (Speed Over Ground)
            # print("im here")
            gpsqual = data.get('gps_qual',0)
            speed = data.get('speed_over_ground', 0.0)
            if speed == None or speed == 0.0:
                
                speed_str = f"{gpsqual} q"
            else:
                speed_kmh = speed * 1.852
                # fused_speed_kmh = kf.update(speed_kmh)
                speed_str = f"{speed_kmh:.2f} km/h"
            
            # current_log_time = time.time()

            # if current_log_time - last_log_time >= 1.0:
            #     timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_log_time))
            #     log_file.write(f"{timestamp},{speed_str}\n")
            #     log_file.flush()  # ensure it's written immediately
            #     last_log_time = current_log_time

            image1 = Image.new('L', (disp.height, disp.width), 0)
            draw = ImageDraw.Draw(image1)
            
            # 4. Draw to Canvas
            rt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((5, 40), rt, font=font_small, fill=15)
            # draw.text((5,40), temp_str, font=font_small, fill=15)
            # draw.text((5, 80), str(a), font=font, fill=15)
            draw.text((20, disp.width//2 + 20), speed_str, font=font_large, fill=15)

  
        image1 = image1.rotate(270)
        # image1 = image1.transpose(Image.FLIP_TOP_BOTTOM)
        disp.ShowImage(disp.getbuffer(image1))
        

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    disp.clear()
    
    disp.module_exit()
    exit()

