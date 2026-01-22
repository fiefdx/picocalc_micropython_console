import gc
import time
import framebuf
import machine
from machine import Pin, SPI, PWM

from ili9488 import Display, color565fast, color565
import lib
import lib.drivers
from lib.ili9488 import ILI9488
from writer import Writer
from font import XglcdFont as Font
from ili9488_111 import Display as Display2
from ili9488_111 import color565 as color5652
from ili9488_111 import color565_inverse
# from ili9488_new import Display as Display2
# from ili9488_new import color565 as color5652
# from ili9488_new import color565_inverse
from display import ILI9488 as Display3
from common import ticks_ms, ticks_add, ticks_diff, sleep_ms

# if machine:
#     machine.freq(250000000)
#     print("freq: %s mhz" % (machine.freq() / 1000000))
    
# fbuf = framebuf.FrameBuffer(bytearray(320 * 320 * 2), 320, 320, framebuf.RGB565) # for RGB-5-6-5
# fbuf = framebuf.FrameBuffer(bytearray(160 * 160 * 2), 160, 160, framebuf.RGB565)
# fbuf = framebuf.FrameBuffer(bytearray(320 * 320), 320, 320, framebuf.GS8) # for RGB-1-1-1

LCD_CS_PIN = 13   # Chip Select
LCD_DC_PIN = 14   # Data/Command
LCD_RST_PIN = 15  # Reset
LCD_SCK_PIN = 10  # SPI Clock
LCD_MOSI_PIN = 11 # SPI Data Out
LCD_BL_PIN = 12   # Backlight Control (Active High)

LCD_WIDTH = 320  # Display width in pixels
LCD_HEIGHT = 320 # Display height in pixels (Square display)

SPI_BUS = 1 # Use SPI1 (matches schematic pins GP10, GP11)
SPI_BAUDRATE = 75_000_000 # SPI clock frequency

# display = Display(spi_bus=SPI_BUS,
#                   cs_pin=LCD_CS_PIN, dc_pin=LCD_DC_PIN, rst_pin=LCD_RST_PIN,
#                   bl_pin=LCD_BL_PIN, sck_pin=LCD_SCK_PIN, mosi_pin=LCD_MOSI_PIN,
#                   width=LCD_WIDTH, height=LCD_HEIGHT, baudrate=SPI_BAUDRATE)
# 
# display.fill_screen(color565(255, 255, 255))
# # display.fill_rect(0, 0, 160, 160, 0xf800)
# # display.fill_rect(160, 160, 160, 160, 0x07e0)
# # display.fill_rect(0, 160, 160, 160,0x001f)
# # display.fill_rect(160, 0, 160, 160, 0xffff)
# 
# parts = [(0, 0), (0, 160), (160, 160), (160, 0)]
# colors = [0xf800, 0x07e0, 0x001f, 0xffff]
# c = 0
# for i in range(10):
#     c = i % 4
#     for p in range(4):
#         display.fill_rect(parts[p][0], parts[p][1], 160, 160, colors[c])
#         c += 1
#         if c >= 4:
#             c = 0
#     time.sleep(0.1)
# 
# # p = Pin(LCD_BL_PIN, Pin.OUT)
# # p.off()
# cs = machine.Pin(LCD_CS_PIN, machine.Pin.OUT, value=1) # CS inactive (high)
# dc = machine.Pin(LCD_DC_PIN, machine.Pin.OUT)
# rst = machine.Pin(LCD_RST_PIN, machine.Pin.OUT)
# # bl = machine.Pin(bl_pin, machine.Pin.OUT)
# # bl_pin_num = bl_pin # Store the pin number
# sck = machine.Pin(LCD_SCK_PIN)
# mosi = machine.Pin(LCD_MOSI_PIN)
# # rst.on()
# # time.sleep(0.1)
# # rst.off()
# spi = machine.SPI(SPI_BUS, baudrate=SPI_BAUDRATE, sck=sck, mosi=mosi)
# # time.sleep(0.1)
# display = ILI9488(spi, cs, dc, rst, height=320, width=320)
# # display.text("this is a test", 60, 60, ILI9488.rgb(0, 255, 0))
# # print(hex(ILI9488.rgb(255, 0, 0)))
# display.fill(0xf800)
# 
# wri = Writer(display, font8)
# wri.wrap = False
# 
# Writer.set_textpos(display, 60, 60)
# wri.printstring("this is a test", 0xf800)
# 
# fbuf = framebuf.FrameBuffer(bytearray(60 * 60 * 2), 60, 60, framebuf.RGB565) # Adjust format as needed
# fbuf.rect(10, 10, 50, 50, ILI9488.rgb(0, 255, 0)) # Draw a white rectangle
# display.blit(fbuf, 60, 60) # Blit to screen
# 
# # display.rect(60, 60, 60, 60, 0xf80000, False)
# display.show()
# # while True:
# # #     p.off()
# #     display.rect(60, 60, 60, 60, 0xf800, False)
# #     print(display.show())
# # #     time.sleep(0.1)
# #

# F58 = Font("/Bally5x8.c", 5, 8)
# cs = machine.Pin(LCD_CS_PIN, machine.Pin.OUT, value=1) # CS inactive (high)
# dc = machine.Pin(LCD_DC_PIN, machine.Pin.OUT)
# rst = machine.Pin(LCD_RST_PIN, machine.Pin.OUT)
# # bl = machine.Pin(bl_pin, machine.Pin.OUT)
# # bl_pin_num = bl_pin # Store the pin number
# sck = machine.Pin(LCD_SCK_PIN)
# mosi = machine.Pin(LCD_MOSI_PIN)
# spi = machine.SPI(SPI_BUS, baudrate=SPI_BAUDRATE, sck=sck, mosi=mosi)
# machine.freq(250000000, 250000000)
# spi.init(baudrate=62_500_000)
# print(dir(spi))
# print("spi.freq: ", spi)
# display = Display2(spi, cs, dc, rst, height=320, width=320, rotation=180)
# #display.fill_vrect(60, 60, 60, 60, color565(255, 0, 0))
# parts = [(0, 0), (0, 160), (160, 160), (160, 0)]
# colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
# lines = []
# for i in range(10):
#     lines.append(i * 40)
# c = 0
# for i in range(20):
#     c = i % 4
#     for p in range(4):
#         display.fill_hrect(parts[p][0], parts[p][1], 160, 160, color565_inverse(*colors[c])) # 0b1000111100000000 blue # 0b111000000001110 green
#         c += 1
#         if c >= 4:
#             c = 0
#     time.sleep(0.1)
# fbuf = framebuf.FrameBuffer(bytearray(320 * 320 * 2), 320, 320, framebuf.RGB565)

# # test for RGB-5-6-5
# c = 0
# for i in range(20):
#     c = i % 4
#     for p in range(4):
#         t = ticks_ms()
#         fbuf.fill(color565_inverse(*colors[c]))
#         display.block(0, 0, 319, 319, fbuf)
#         print((ticks_ms() - t) / 1000.0)
#         c += 1
#         if c >= 4:
#             c = 0

# # test for RGB-1-1-1
# colors = [0b00000100 ^ 0xff, 0b00000010 ^ 0xff, 0b00000001 ^ 0xff, 0b00000000 ^ 0xff, 0b00000111 ^ 0xff, 0b00000101 ^ 0xff, 0b00000110 ^ 0xff, 0b00000011 ^ 0xff]
# for i in range(10):
#     c = i % 4
#     for p in range(4):
#         t = ticks_ms()
#         fbuf.fill(colors[p])
#         display.block(0, 0, 319, 319, fbuf)
#         print((ticks_ms() - t) / 1000.0)
#         c += 1
#         if c >= 4:
#             c = 0
# fbuf.text("this is a test", 0, 0, 0b00000111^0xff)
# for x in range(8):
#     fbuf.rect(40 * x , 10, 40, 40, colors[x], True)
# colors = [0b11111000, 0b00000010, 0b00000001, 0b00000000, 0b00000111, 0b00000101, 0b00000110, 0b00000011]
# for x in range(8):
#     fbuf.rect(40 * x , 50, 40, 40, colors[x], True)
# display.block(0, 0, 319, 319, fbuf)



# display.clear(color565_inverse(0, 0, 0))
# display.fill_circle(160, 160, 60, 0x07e0^0xffff)
# display.draw_text8x8(0, 0, "this is a test", color565_inverse(255, 0, 0), background=color565_inverse(0, 0, 0), rotate=0)
# display.draw_text(0, 300, "this is another test!", F58, color565_inverse(255, 0, 0), background=color565_inverse(0, 0, 0), landscape=False, spacing=1)
# display.clear(color565_inverse(0, 0, 0))
# n = 0
# for i in range(20):
#     t = time.time()
#     for l in range(41):
#         display.draw_text(0, l * 8 + 1, str(n) * 53, F58, color565_inverse(255, 255, 255), background=color565_inverse(0, 0, 0), landscape=False, spacing=1)
#         n += 1
#         if n >= 10:
#             n = 0
#     print("using: %fs" % (time.time() - t))


# buf = bytearray(320 * 320)
# l = 320 * 320
# colors = [0b00100100 ^ 0xff, 0b00010010 ^ 0xff, 0b00001001 ^ 0xff, 0b00111111 ^ 0xff]
# for i in range(20):
#     for p in range(4):
#         t = ticks_ms()
#         gc.collect()
# #         buf = bytearray([colors[p]] * l)
# #         buf = bytearray([0b00000100 ^ 0xff] * l)
#         for b in range(len(buf)):
#             buf[b] = colors[p]
#         display.block(0, 0, 319, 319, buf)
#         print((ticks_ms() - t) / 1000.0)
# #         time.sleep(0.1)


cs = machine.Pin(LCD_CS_PIN, machine.Pin.OUT, value=1) # CS inactive (high)
dc = machine.Pin(LCD_DC_PIN, machine.Pin.OUT)
rst = machine.Pin(LCD_RST_PIN, machine.Pin.OUT)
# bl = machine.Pin(bl_pin, machine.Pin.OUT)
# bl_pin_num = bl_pin # Store the pin number
sck = machine.Pin(LCD_SCK_PIN)
mosi = machine.Pin(LCD_MOSI_PIN)
spi = machine.SPI(SPI_BUS, baudrate=SPI_BAUDRATE, sck=sck, mosi=mosi)
machine.freq(250000000, 250000000)
spi.init(baudrate=62_500_000)
print(dir(spi))
print("spi.freq: ", spi)
display = Display3(spi, cs, dc, rst, height=320, width=320)
parts = [(0, 0), (0, 160), (160, 160), (160, 0)]
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
colors = [0b00000100 ^ 0xff, 0b00000010 ^ 0xff, 0b00000001 ^ 0xff, 0b00000000 ^ 0xff, 0b00000111 ^ 0xff, 0b00000101 ^ 0xff, 0b00000110 ^ 0xff, 0b00000011 ^ 0xff]
for i in range(10):
    c = i % 4
    for p in range(4):
        t = ticks_ms()
        display.fill(colors[p])
        display.show()
        print((ticks_ms() - t) / 1000.0)
        c += 1
        if c >= 4:
            c = 0
display.text("this is a test", 0, 0, display.rgb(1, 0, 0))
for x in range(8):
    display.rect(40 * x , 10, 40, 40, colors[x], True)
colors = [0b11111000, 0b00000010, 0b00000001, 0b00000000, 0b00000111, 0b00000101, 0b00000110, 0b00000011]
for x in range(8):
    display.rect(40 * x , 50, 40, 40, colors[x], True)
# display.text("nnnnnnnnnnnnnnn", 0, 0, display.rgb(0, 0, 0))
display.show()
t = ticks_ms()
display.scroll(0, 8)
display.rect(0, 0, 320, 8, display.rgb(0, 0, 0), True)
display.show()
print((ticks_ms() - t) / 1000)
for i in range(40):
    display.scroll(0, 8)
    display.rect(0, 0, 320, 8, display.rgb(0, 0, 0), True)
    display.show()
#     time.sleep(0.1)

