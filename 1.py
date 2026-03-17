from bmp280 import BMP280
from smbus2 import SMBus
import time
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')


import logging    
import traceback
from waveshare_OLED import OLED_1in32
from PIL import Image,ImageDraw,ImageFont
logging.basicConfig(level=logging.DEBUG)

I2C_BUS = 1
I2C_ADDR = 0x76  # change to 0x77 if your sensor shows 77 in i2cdetect

bus = SMBus(I2C_BUS)
bmp = BMP280(i2c_dev=bus, i2c_addr=0x76)

try:
    # time.sleep(60)
    disp = OLED_1in32.OLED_1in32()


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

        # # Create blank image for drawing.
        # image1 = Image.new('L', (disp.height, disp.width), 0)
        # draw = ImageDraw.Draw(image1)
        # font = ImageFont.truetype('Font.ttc',15)
        

        # temp_c = bmp.get_temperature()
        # # temp_c = 22
        # temp_str = f"{temp_c:.2f}"
        # pressure_hpa = bmp.get_pressure()
        # qnh = 1015
        # pressure_pa = pressure_hpa*100.0
        # altitude_m = (((qnh/pressure_hpa)**(1.0/5.257)-1.0)*(temp_c+273))/0.0065
        # alt_str = f"{altitude_m:.2f} m"

        #     # 4. Draw to Canvas
        # draw.text((5, 20), "Temp", font=font, fill=15)
        # draw.text((5, 40), temp_str, font=font, fill=15)
        # # draw.text((10, 60), , font=font, fill=15)

        # draw.text((20, 60), "Altitude ()", font=font, fill=15)
        # draw.text((20, 80), alt_str, font=font, fill=15)
        
        

        # # logging.info ("***draw line")
        # # draw.line([(0,0),(95,0)], fill = 15)
        # # draw.line([(0,0),(0,127)], fill = 15)
        # # draw.line([(0,127),(95,127)], fill = 15)
        # # draw.line([(95,0),(95,127)], fill = 15)
        # # logging.info ("***draw text")
        # # draw.text((20,2), 'Hello', font = font1, fill = 13)
  
        # image1 = image1.rotate(270)
        # disp.ShowImage(disp.getbuffer(image1))
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



    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    disp.clear()
    disp.module_exit()
    exit()



    
    
    #altitude_m = bmp.get_altitude()
    qnh = 1015
    altitude_m = (((qnh/pressure_hpa)**(1.0/5.257)-1.0)*(temp_c+273))/0.0065

    pressure_pa = pressure_hpa*100.0

    print(f"Temp: {temp_c:6.2f} °C | Pressure: {pressure_pa:9.2f} Pa | Altitude: {altitude_m:7.2f} m")
    time.sleep(1)


