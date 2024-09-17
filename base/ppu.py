from base.memory import *
import numpy
class OMAEntry:
    def __init__(self) -> None:
        pass
class PPUState:
    OAM_SCAN = 2
    DRAWING = 3
    HBLANK = 0
    VBLANK = 1

class PixelFecherState:
    GET_TILE_ID = 0
    GET_TILE_DATA_LOW = 1
    GET_TILE_DATA_HIGHT = 2
    PUSH = 3

class FIFO():
    def __init__(self) -> None:
        self.array = []
        pass
    def push(self, value):
        self.array.append(value)
    def pop(self):
        return self.array.pop(0)
    def length(self):
        return len(self.array)


class PixelFecher:
    def __init__(self, ly, fifo, vram) -> None:
        self.vram: Memory= vram
        self.fifo = fifo
        self.ly = ly
        self.tile_line = ly % 8
        self.data = numpy.zeros(8, numpy.int8)

        self.ticks = 0
        self.state = PixelFecherState.GET_TILE_ID
        self.tile_offset_in_bg_map = 0
        self.tile_offset_in_line = 0
        self.tile_id = 0
        pass
    def tick(self):
        if self.ticks < 2:
            self.ticks += 1
            return
        self.ticks = 0
        match self.state:
            case PixelFecherState.GET_TILE_ID:
                self.tile_offset_in_bg_map = (self.ly // 8) * 32 + self.tile_offset_in_line
                self.tile_id = self.vram.read(0x9800 + self.tile_offset_in_bg_map)
                self.state = PixelFecherState.GET_TILE_DATA_LOW
            case PixelFecherState.GET_TILE_DATA_LOW:
                addr_tile = 0x8000 + (self.tile_id * 16)
                tile_line_data_addr = addr_tile + self.tile_line * 2
                for i in range(0, 8):
                    low = self.vram.read(tile_line_data_addr)
                    self.data[i] = (low >> (8 - i)) & 1
                self.state = PixelFecherState.GET_TILE_DATA_HIGHT
            case PixelFecherState.GET_TILE_DATA_HIGHT:
                addr_tile = 0x8000 + (self.tile_id * 16)
                tile_line_data_addr = addr_tile + self.tile_line * 2
                for i in range(0, 8):
                    high = self.vram.read(tile_line_data_addr)
                    self.data[i] = self.data[i] | ((high >> (8 - i)) & 1) << 1
                self.state = PixelFecherState.PUSH
            case PixelFecherState.PUSH:
                if self.fifo.length() == 0:
                    for pixel in self.data:
                        self.fifo.push(pixel)
                    self.state = PixelFecherState.GET_TILE_ID
                    self.tile_offset_in_line += 1
class Ppu:
    WIDTH = 160
    HIGHT = 144
    def __init__(self) -> None:
        self.vram = RAM(0x8000, 0x9FFF)
        self.state = PPUState.OAM_SCAN
        
        self.frame = numpy.zeros([160, 144])
        # ------------------
        # LCDC
        obj_enable = 1
        obj_size = 0
        bg_tile_map = 0
        bg_window_map = 0
        window_enable = 0
        window_tile_map = 0
        lcd_ppu_enable = 1
        # ------------------
        self.ly = 0
        self.lyc = 0
        self.stat = 0

        self.scy = 0
        self.scx = 0
        self.wx = 7
        self.wy = 0

        self.bgp = 0
        self.obp0 = 0
        self.obp = 0

        self.current_oam_buffer = numpy.zeros(10)
        self.oam_buffer_index = 0
        self.ticks = 0

        # ---- Fifo
        self.isFrameReady = False
        self.fetcher = None
        self.x = 0
        self.bg_fifo = FIFO()

        pass
    def dot(self):
        pass
    def oam_scan_on_addr(self, addr):
        if self.oam_buffer_index < 10:
            sprite_x = self.vram.read(addr)
            sprite_y = self.vram.read(addr + 1)
            if sprite_x > 0 and self.ly + 16 >= sprite_y and self.ly < sprite_y + 8:
                self.current_oam_buffer[self.current_oam_buffer] = addr
    def tick(self):
        self.ticks += 1
        # print(self.ticks, self.state)
        match self.state:
            case PPUState.OAM_SCAN:
                if self.ticks < 80:
                    return
                # addr = 0xFE00
                # while addr < 0xFEA0:
                #     self.oam_scan_on_addr(addr)
                #     addr += 0x04
                self.x = 0
                self.state = PPUState.DRAWING
            case PPUState.DRAWING:
                if self.fetcher == None:
                    self.fetcher = PixelFecher(self.ly, self.bg_fifo, self.vram)
                self.fetcher.tick()
                if self.bg_fifo.length() == 0:
                    return
                pixel = self.bg_fifo.pop()
                self.frame[self.x, self.ly] = pixel
                self.x += 1
                if self.x == 160:
                    self.fetcher = None
                    self.state = PPUState.HBLANK
            case PPUState.HBLANK:
                if self.ticks == 456:
                    self.ticks = 0
                    self.ly += 1
                    if self.ly == Ppu.HIGHT:
                        self.state = PPUState.VBLANK
                        self.isFrameReady = True
                    else:
                        self.state = PPUState.OAM_SCAN
            case PPUState.VBLANK:
                if self.ticks == 456:
                    self.ticks = 0
                    self.ly += 1
                    if self.ly == 153:
                        self.ly = 0
                        self.state = PPUState.OAM_SCAN
                        self.isFrameReady = False

class LCDVIDEOMemory(Memory):
    def __init__(self, ppu: Ppu) -> None:
        self.ppu = ppu
        pass
    def inside(self, addr):
        return self.ppu.vram.inside(addr)
    def read(self, addr):
        return self.ppu.vram.read(addr)
    def write(self, addr, value):
        self.ppu.vram.write(addr, value)
