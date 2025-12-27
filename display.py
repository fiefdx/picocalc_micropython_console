import gc
import framebuf
import ustruct
from time import sleep_ms

RGB565 = const(0x00)
RGB111 = const(0x01)


class BoolPalette(framebuf.FrameBuffer):

    def __init__(self, mode):
        buf = bytearray(4)  # OK for <= 16 bit color
        super().__init__(buf, 2, 1, mode)
    
    def fg(self, color):  # Set foreground color
        self.pixel(1, 0, color)

    def bg(self, color):
        self.pixel(0, 0, color)


class Colors(object):
    white = None   # 1,1,1
    black = None   # 0,0,0
    red = None     # 1,0,0
    green = None   # 0,1,0
    blue = None    # 0,0,1
    cyan = None    # 0,1,1
    magenta = None # 1,0,1
    yellow = None  # 1,1,0


class ILI9488(framebuf.FrameBuffer):
    NOP = const(0x00)  # No-op
    SWRESET = const(0x01)  # Software reset
    RDDID = const(0x04)  # Read display ID info
    RDDST = const(0x09)  # Read display status
    SLPIN = const(0x10)  # Enter sleep mode
    SLPOUT = const(0x11)  # Exit sleep mode
    PTLON = const(0x12)  # Partial mode on
    NORON = const(0x13)  # Normal display mode on
    RDMODE = const(0x0A)  # Read display power mode
    RDMADCTL = const(0x0B)  # Read display MADCTL
    RDPIXFMT = const(0x0C)  # Read display pixel format
    RDIMGFMT = const(0x0D)  # Read display image format
    RDSELFDIAG = const(0x0F)  # Read display self-diagnostic
    INVOFF = const(0x20)  # Display inversion off
    INVON = const(0x21)  # Display inversion on
    GAMMASET = const(0x26)  # Gamma set
    DISPLAY_OFF = const(0x28)  # Display off
    DISPLAY_ON = const(0x29)  # Display on
    SET_COLUMN = const(0x2A)  # Column address set
    SET_PAGE = const(0x2B)  # Page address set
    WRITE_RAM = const(0x2C)  # Memory write
    READ_RAM = const(0x2E)  # Memory read
    PTLAR = const(0x30)  # Partial area
    VSCRDEF = const(0x33)  # Vertical scrolling definition
    MADCTL = const(0x36)  # Memory access control
    VSCRSADD = const(0x37)  # Vertical scrolling start address
    PIXFMT = const(0x3A)  # COLMOD: Pixel format set
    WRITE_DISPLAY_BRIGHTNESS = const(0x51)  # Brightness hardware dependent!
    READ_DISPLAY_BRIGHTNESS = const(0x52)
    WRITE_CTRL_DISPLAY = const(0x53)
    READ_CTRL_DISPLAY = const(0x54)
    WRITE_CABC = const(0x55)  # Write Content Adaptive Brightness Control
    READ_CABC = const(0x56)  # Read Content Adaptive Brightness Control
    WRITE_CABC_MINIMUM = const(0x5E)  # Write CABC Minimum Brightness
    READ_CABC_MINIMUM = const(0x5F)  # Read CABC Minimum Brightness
    FRMCTR1 = const(0xB1)  # Frame rate control (In normal mode/full colors)
    FRMCTR2 = const(0xB2)  # Frame rate control (In idle mode/8 colors)
    FRMCTR3 = const(0xB3)  # Frame rate control (In partial mode/full colors)
    INVCTR = const(0xB4)  # Display inversion control
    DFUNCTR = const(0xB6)  # Display function control
    PWCTR1 = const(0xC0)  # Power control 1
    PWCTR2 = const(0xC1)  # Power control 2
    PWCTRA = const(0xCB)  # Power control A
    PWCTRB = const(0xCF)  # Power control B
    VMCTR1 = const(0xC5)  # VCOM control 1
    VMCTR2 = const(0xC7)  # VCOM control 2
    RDID1 = const(0xDA)  # Read ID 1
    RDID2 = const(0xDB)  # Read ID 2
    RDID3 = const(0xDC)  # Read ID 3
    RDID4 = const(0xDD)  # Read ID 4
    GMCTRP1 = const(0xE0)  # Positive gamma correction
    GMCTRN1 = const(0xE1)  # Negative gamma correction
    DTCA = const(0xE8)  # Driver timing control A
    DTCB = const(0xEA)  # Driver timing control B
    POSC = const(0xED)  # Power on sequence control
    ENABLE3G = const(0xF2)  # Enable 3 gamma control
    PUMPRC = const(0xF7)  # Pump ratio control

    ROTATE = (0x88, 0xE8, 0x48, 0x28)
    
    def __init__(self, spi, cs, dc, rst, width = 320, height = 320, rotation = 180, color_mode = RGB111):
        """Initialize Display.
        Args:
            spi (Class Spi):  SPI interface for display
            cs (Class Pin):  Chip select pin
            dc (Class Pin):  Data/Command pin
            rst (Class Pin):  Reset pin
            width (Optional int): Screen width (default 320)
            height (Optional int): Screen height (default 320)
            rotation (Optional int): Rotation must be 180 default, 90. 180 or 270
        """
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = width
        self.height = height
        if rotation // 90 >= 4:
            raise RuntimeError('Rotation must be 0, 90, 180 or 270.')
        else:
            self.rotation = self.ROTATE[rotation // 90]
        self.color_mode = color_mode
        self.mode = framebuf.RGB565 if self.color_mode == RGB565 else framebuf.GS8
        self.palette = BoolPalette(self.mode)
        gc.collect()
        self.buffer = bytearray(height * width * 2 if self.color_mode == RGB565 else height * width)
        self.mvb = memoryview(self.buffer)
        super().__init__(self.buffer, width, height, framebuf.RGB565 if self.color_mode == RGB565 else framebuf.GS8)
        self.rgb = self.rgb565 if self.color_mode == RGB565 else self.rgb111
        Colors.white = self.rgb(255, 255, 255) if self.color_mode == RGB565 else self.rgb(1, 1, 1)
        Colors.black = self.rgb(0, 0, 0) if self.color_mode == RGB565 else self.rgb(0, 0, 0)
        Colors.red = self.rgb(255, 0, 0) if self.color_mode == RGB565 else self.rgb(1, 0, 0)
        Colors.green = self.rgb(0, 255, 0) if self.color_mode == RGB565 else self.rgb(0, 1, 0)
        Colors.blue = self.rgb(0, 0, 255) if self.color_mode == RGB565 else self.rgb(0, 0, 1)
        Colors.cyan = self.rgb(0, 255, 255) if self.color_mode == RGB565 else self.rgb(0, 1, 1)
        Colors.magenta = self.rgb(255, 0, 255) if self.color_mode == RGB565 else self.rgb(1, 0, 1)
        Colors.yellow = self.rgb(255, 255, 0) if self.color_mode == RGB565 else self.rgb(1, 1, 0)

        # Initialize GPIO pins and set implementation specific methods
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)
        self.reset()
        # Send initialization commands
        self.write_cmd(self.SWRESET)  # Software reset
        sleep_ms(100)
        self.write_cmd(self.PWCTRB, 0x00, 0xC1, 0x30)  # Pwr ctrl B
        self.write_cmd(self.POSC, 0x64, 0x03, 0x12, 0x81)  # Pwr on seq. ctrl
        self.write_cmd(self.DTCA, 0x85, 0x00, 0x78)  # Driver timing ctrl A
        self.write_cmd(self.PWCTRA, 0x39, 0x2C, 0x00, 0x34, 0x02)  # Pwr ctrl A
        self.write_cmd(self.PUMPRC, 0x20)  # Pump ratio control
        self.write_cmd(self.DTCB, 0x00, 0x00)  # Driver timing ctrl B
        self.write_cmd(self.PWCTR1, 0x23)  # Pwr ctrl 1
        self.write_cmd(self.PWCTR2, 0x10)  # Pwr ctrl 2
        self.write_cmd(self.VMCTR1, 0x3E, 0x28)  # VCOM ctrl 1
        self.write_cmd(self.VMCTR2, 0x86)  # VCOM ctrl 2
        self.write_cmd(self.MADCTL, self.rotation)  # Memory access ctrl
        self.write_cmd(self.VSCRSADD, 0x00)  # Vertical scrolling start address
        self.write_cmd(self.PIXFMT, 0x02)  # COLMOD: Pixel format
        self.write_cmd(self.FRMCTR1, 0xA0, 0x11)  # Frame rate ctrl
        self.write_cmd(self.DFUNCTR, 0x02,0x02)
        self.write_cmd(self.ENABLE3G, 0x00)  # Enable 3 gamma ctrl
        self.write_cmd(self.GAMMASET, 0x01)  # Gamma curve selected
        self.write_cmd(self.GMCTRP1, 0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E,
                       0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)
        self.write_cmd(self.GMCTRN1, 0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31,
                       0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)
        self.write_cmd(0x35)
        self.write_cmd(self.SLPOUT)  # Exit sleep
        sleep_ms(100)
        self.write_cmd(self.DISPLAY_ON)  # Display on
        sleep_ms(100)
        self.clear()
        
    def rgb111(self, r, g, b): # for RGB-1-1-1: r = 1/0, g = 1/0, b = 1/0
        return 0xff ^ (r << 2 | g << 1 | b)
    
    def rgb565(self, r, g, b): # for RGB-565: r = 0~255, g = 0~255, b = 0~255
        return 0xffff ^ ((r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3)
        
    def reset(self):
        """Perform reset: Low=initialization, High=normal operation.
        """
        self.rst(0)
        sleep_ms(50)
        self.rst(1)
        sleep_ms(50)
        
    def write_cmd(self, command, *args):
        """Write command to OLED (MicroPython).
        Args:
            command (byte): ILI9488 command code.
            *args (optional bytes): Data to transmit.
        """
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        # Handle any passed data
        if len(args) > 0:
            self.write_data(bytearray(args))
            
    def write_data(self, data):
        """Write data to OLED (MicroPython).
        Args:
            data (bytes): Data to transmit.
        """
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)
        
    def block(self, x0, y0, x1, y1, data):
        """Write a block of data to display.
        Args:
            x0 (int):  Starting X position.
            y0 (int):  Starting Y position.
            x1 (int):  Ending X position.
            y1 (int):  Ending Y position.
            data (bytes): Data buffer to write.
        """
        self.write_cmd(self.SET_COLUMN, *ustruct.pack(">HH", x0, x1))
        self.write_cmd(self.SET_PAGE, *ustruct.pack(">HH", y0, y1))

        self.write_cmd(self.WRITE_RAM)
        self.write_data(data)

    def cleanup(self):
        """Clean up resources."""
        self.clear()
        self.display_off()
        self.spi.deinit()
        print('display off')

    def clear(self, color=0):
        """Clear display.
        Args:
            color (Optional int): RGB565 color value (Default: 0 = Black).
        """
        w = self.width
        h = self.height
        # Clear display in 1024 byte blocks
        if color is not None:
            line = color.to_bytes(2, 'big') * (w * 8)
        else:
            line = bytearray(w * 16)
        for y in range(0, h, 8):
            self.block(0, y, w - 1, y + 7, line)

    def display_off(self):
        """Turn display off."""
        self.write_cmd(self.DISPLAY_OFF)

    def display_on(self):
        """Turn display on."""
        self.write_cmd(self.DISPLAY_ON)
        
    def vscroll(self, y):
        """Scroll display vertically.
        Args:
            y (int): Number of pixels to scroll display.
        """
        self.write_cmd(self.VSCRSADD, y >> 8, y & 0xFF)

    def set_vscroll(self, top, bottom):
        """Set the height of the top and bottom scroll margins.
        Args:
            top (int): Height of top scroll margin
            bottom (int): Height of bottom scroll margin
        """
        if top + bottom <= self.height:
            middle = self.height - (top + bottom)
            print(top, middle, bottom)
            self.write_cmd(self.VSCRDEF,
                           top >> 8,
                           top & 0xFF,
                           middle >> 8,
                           middle & 0xFF,
                           bottom >> 8,
                           bottom & 0xFF)

    def sleep(self, enable=True):
        """Enters or exits sleep mode.
        Args:
            enable (bool): True (default)=Enter sleep mode, False=Exit sleep
        """
        if enable:
            self.write_cmd(self.SLPIN)
        else:
            self.write_cmd(self.SLPOUT)
            
    def show(self):
        self.block(0, 0, self.width, self.height, self)
        
    def clear_line(self, x, y, color, line_height = 8, width_offset = 0, x_offset = 0, y_offset = 0, length = 40, font_width = 8):
        self.rect(x + x_offset, y + y_offset, length * font_width + width_offset, line_height, color, True)
