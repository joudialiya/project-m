from base.memory import *
from base.bitwise_alu_operations import to_signed_d8
from base.interrupts import InterruptContext
import numpy
import time
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
    def __init__(self, ly, fifo, vram, addressing_mode) -> None:
        self.addresing_mode = addressing_mode 
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
    def tile_address(self):
        if self.addresing_mode == 1:
            return 0x8000 + (self.tile_id * 16)
        return 0x9000 + (to_signed_d8(self.tile_id) * 16)
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
                addr_tile = self.tile_address()
                tile_line_data_addr = addr_tile + self.tile_line * 2
                for i in range(0, 8):
                    low = self.vram.read(tile_line_data_addr)
                    self.data[i] = (low >> (7 - i)) & 1
                self.state = PixelFecherState.GET_TILE_DATA_HIGHT
            case PixelFecherState.GET_TILE_DATA_HIGHT:
                addr_tile = self.tile_address() + 1
                tile_line_data_addr = addr_tile + self.tile_line * 2
                for i in range(0, 8):
                    high = self.vram.read(tile_line_data_addr)
                    self.data[i] = self.data[i] | ((high >> (7 - i)) & 1) << 1
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

    # STAT bit offsets ----
    LY_EQ_LYC = 2
    ENABLE_M_0 = 3
    ENABLE_M_1 = 4
    ENABLE_M_2 = 5
    ENABLE_LYC_COMPARE = 6
    # STAT bit offsets ----

    def __init__(self, vram: RAM, oam_ram: RAM, interrupt_context: InterruptContext) -> None:
        self.interrupt_context = interrupt_context
        self.vram = vram
        self.oam_ram = oam_ram

        
        self.frame = numpy.zeros([160, 144])
        # ------------------
        # LCDC
        self.lcdc = 0
        # obj_enable = 1
        # obj_size = 0
        # bg_tile_map = 0
        # bg_window_map = 0
        # window_enable = 0
        # window_tile_map = 0
        # lcd_ppu_enable = 1
        # ------------------
        self.ly = 0
        self.lyc = 0

        # STAT register ----
        self.state = PPUState.OAM_SCAN
        self.lyc_compare = False
        self.enable_lyc_compare = False
        self.enable_m0 = False
        self.enable_m1 = False
        self.enable_m2 = False
        # STAT register ----
        self.stat_prev_signal = 0

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
        # ---- Fifo
        self.last_frame_time = time.time()
        pass

    def oam_scan_on_addr(self, addr):
        if self.oam_buffer_index < 10:
            sprite_x = self.vram.read(addr)
            sprite_y = self.vram.read(addr + 1)
            if sprite_x > 0 and self.ly + 16 >= sprite_y and self.ly < sprite_y + 8:
                self.current_oam_buffer[self.current_oam_buffer] = addr
    def attempt_lcd_interrupt(self):
        # This signal is set to 1 if:
        # ( (LY = LYC) AND (STAT.ENABLE_LYC_COMPARE = 1) ) OR
        # ( (ScreenMode = 0) AND (STAT.ENABLE_HBL = 1) ) OR
        # ( (ScreenMode = 2) AND (STAT.ENABLE_OAM = 1) ) OR
        # ( (ScreenMode = 1) AND (STAT.ENABLE_VBL || STAT.ENABLE_OAM) ) -
        current_signal = (
            (self.enable_m0 and (self.state == PPUState.HBLANK)) or
            (self.enable_m1 and (self.state == PPUState.VBLANK)) or
            (self.enable_m2 and (self.state == PPUState.OAM_SCAN)) or
            (self.enable_lyc_compare and (self.lyc == self.ly))
        )
        if current_signal and not self.stat_prev_signal:
            self.interrupt_context.setRequested(InterruptContext.LCD, True)
        self.stat_prev_signal = current_signal
    def get_stat(self):
        result = self.state & 0b11
        if self.ly == self.lyc:
            result |= 1 << Ppu.LY_EQ_LYC
        if self.state == PPUState.HBLANK:
            result |= 1 << Ppu.ENABLE_M_0
        if self.state == PPUState.VBLANK:
            result |= 1 << Ppu.ENABLE_M_1
        if self.state == PPUState.OAM_SCAN:
            result |= 1 << Ppu.ENABLE_M_2
        if self.enable_lyc_compare:
            result |= 1 << Ppu.ENABLE_LYC_COMPARE
        return result
    def set_stat(self, value):
        self.enable_lyc_compare = ((value >> Ppu.ENABLE_LYC_COMPARE) & 1) == 1
        self.enable_m0= ((value >> Ppu.ENABLE_M_0) & 1) == 1
        self.enable_m1 = ((value >> Ppu.ENABLE_M_1) & 1) == 1
        self.enable_m2 = ((value >> Ppu.ENABLE_M_2) & 1) == 1
        

    def tick(self):
        self.ticks += 1
        self.attempt_lcd_interrupt()
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
                    self.fetcher = PixelFecher(
                        self.ly,
                        self.bg_fifo,
                        self.vram,
                        (self.lcdc >> 4) & 1)
                self.fetcher.tick()
                if self.bg_fifo.length() == 0:
                    return
                pixel = self.bg_fifo.pop()
                self.frame[self.x, self.ly] = (self.bgp >> (pixel * 2)) & 0b11
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
                        # ---------------------------------------
                        print(time.time() - self.last_frame_time, 1 / (time.time() - self.last_frame_time))
                        self.last_frame_time = time.time()
                        # ---------------------------------------
                        self.interrupt_context.setRequested(InterruptContext.VBLANK, True)
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

class LCDRegisters(Memory):
    def __init__(self, ppu: Ppu) -> None:
        self.ppu = ppu
        pass
    def inside(self, addr):
        return (addr >= 0xFF40) and (addr <= 0xFF4B)
    def read(self, addr):
        match addr:
            case 0xFF40:
                return self.ppu.lcdc
            case 0xFF41:
                return self.ppu.get_stat()
            case 0xFF42:
                return self.ppu.scy
            case 0xFF43:
                return self.ppu.scx
            case 0xFF44:
                return self.ppu.ly
            case 0xFF45:
                return self.ppu.lyc
            case 0xFF47:
                return self.ppu.bgp        
    def write(self, addr, value):
        match addr:
            case 0xFF40:
                self.ppu.lcdc = value
                print("LCDC: {:08b}".format(value))
            case 0xFF41:
                self.ppu.set_stat(value)
                print("STAT: {:08b}".format(value))
            case 0xFF42:
                self.ppu.scy = value
            case 0xFF43:
                self.ppu.scx = value
            case 0xFF44:
                # dont write the ly
                return
            case 0xFF45:
                self.ppu.lyc = value     
            case 0xFF47:
                self.ppu.bgp = value  
