#!/usr/bin/python
# -*- coding:utf-8 -*-
import time

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

# def gps_prompt():
#     gps = PA1010D()

#     while True:
#         result = gps.update()
#         if result:
#             print("""
#     T: {timestamp}
#     N: {latitude}
#     E: {longitude}
#     Alt: {altitude}
#     Sats: {num_sats}
#     Qual: {gps_qual}
#     Speed: {speed_over_ground}
#     Fix Type: {mode_fix_type}
#     PDOP: {pdop}
#     VDOP: {vdop}
#     HDOP: {hdop}
#     """.format(**gps.data))
#         time.sleep(1.0)

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


    print("speedometer booting")

    logging.info("\r 1.32inch OLED ")


    disp.Init()
    time.sleep(0.2)
    disp.clear()
    time.sleep(0.2)
    disp.Init()
    time.sleep(0.2)
    disp.clear()


    # clear image buffer
    image1 = Image.new('L', (disp.height, disp.width), 0)
    disp.ShowImage(disp.getbuffer(image1))
    time.sleep(0.2)

    while 1:

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
                speed_str = f"{speed_kmh:.2f}"
            

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






