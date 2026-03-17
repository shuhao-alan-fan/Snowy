import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging    
import time
import traceback
from waveshare_OLED import OLED_1in32
from PIL import Image,ImageDraw,ImageFont
logging.basicConfig(level=logging.DEBUG)

import random
import string

def get_random_string(length):
    # Choose from all uppercase and lowercase letters + digits
    characters = string.ascii_letters + string.digits
    result = ''.join(random.choices(characters, k=length))
    return result
    
try:
    disp = OLED_1in32.OLED_1in32()

    print("Initialized display")
    logging.info("\r 1.32inch OLED")
    disp.Init()
    logging.info("clear display")
    disp.clear()

    while 1:
        image1 = Image.new('L',(disp.height, disp.width),0)
        draw = ImageDraw.Draw(image1)

        font_large = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 20)  # speed
        font_small = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 10)  # temp & altitude

        logging.info("*****drawing static texts")

        # Top left - altitude
        draw.text((2, 2), '1270m', font=font_small, fill=15)
        # Top right - temperature
        draw.text((disp.height - 35, 2), '-5°C', font=font_small, fill=15)
        # Bottom centre - speed (large)
        draw.text((disp.height // 2 - 30, disp.width - 28), '36km/h', font=font_large, fill=15)
        
        image1 = image1.rotate(270)
        image1 = image1.transpose(Image.FLIP_TOP_BOTTOM)
        disp.ShowImage(disp.getbuffer(image1))
        time.sleep(3)

    
    disp.clear()

except IOError as e:
    logging.info(e)


    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    disp.module_exit()
    exit()

# !/usr/bin/python
# -*- coding:utf-8 -*-

