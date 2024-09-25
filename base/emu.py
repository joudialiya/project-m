from base.cpu import CyceledCpu
from base.timer import *
from base.interrupts import *
from base.bus import *
from base.ppu import *
from base.memory import *
from base.dma import *
import pygame
import numpy
import time


class Emu:
    def __init__(self, cartridge) -> None:
        self.wram = RAM(0xC000, 0xDFFF)
        self.hram = RAM(0xFF80, 0xFFFE)
        self.oam_ram = RAM(0xFE00, 0xFE9F)
        self.cartridge = cartridge
        self.vram = RAM(0x8000, 0x9FFF)

        self.interrupt_context = InterruptContext()
        self.timer_context = TimerContext(self.interrupt_context)
        self.ppu = Ppu(self.vram, self.oam_ram, self.interrupt_context)
        

        # memory
        self.memory = GlobalMemory()
        self.memory.spaces.append(self.cartridge)
        self.memory.spaces.append(self.vram)
        self.memory.spaces.append(self.oam_ram)
        self.memory.spaces.append(self.wram)
        self.memory.spaces.append(self.hram)
        self.memory.spaces.append(IOMemory())
        self.memory.spaces.append(InteruptEnableRegiter(self.interrupt_context))
        self.memory.spaces.append(InteruptFlagRegister(self.interrupt_context))
        self.memory.spaces.append(TimerRegisters(self.timer_context))
        self.memory.spaces.append(LCDRegisters(self.ppu))

        self.dma_context = DmaContext(self.memory)
        self.memory.spaces.append(DMARegister(self.dma_context))

        self.cpu = CyceledCpu(
            self.timer_context,
            self.interrupt_context,
            self.memory
        )
        self.memory.index_spaces()
        self.clock = 0
        pass
    def step_by_instruction(self):
        while(True):
            self.tick()
            # if self.cpu.isHalted:
            #     print("DIV: {:04X} TIMA: {:02X} TMA: {:02X} TAC: {:08b}".format(
            #         self.timer_context.div,
            #         self.timer_context.tima,
            #         self.timer_context.tma,
            #         self.timer_context.tac))
            if self.cpu.passed_by_feaching or self.cpu.isHalted:
                # print("{:04X}".format(self.cpu.current_pc))
                break

    def tile_to_surface_with_numpy(self, addr):
        array = numpy.zeros([8, 8])

        for line in range(0, 8):
            offset_addr = addr + 2 * line
            low, high = self.memory.read(offset_addr), self.memory.read(offset_addr + 1)
            for x in range(0, 8):
                array[x, line] = ((low >> (7 - x)) & 1) | (((high >> (7 - x)) & 1) << 1)
                pass
        tile = pygame.surfarray.make_surface(array)
        tile.set_palette([
            [0xff, 0xff, 0xff], 
            [0x7e, 0x7e, 0x7e], 
            [0xbd, 0xbd, 0xbd], 
            [0x00, 0x00, 0x00]])
        return tile

    def render(self):
        # pygame setup
        pygame.init()
        screen = pygame.display.set_mode((600, 600))
        clock = pygame.time.Clock()
        running = True
        vram_view = pygame.Surface([16 * 8, 24 * 8], depth=8)

        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # fill the screen with a color to wipe away anything from last frame
            screen.fill("purple")


            if self.ppu.isFrameReady:
                addr = 0x8000
                while addr < 0x9800:
                    tile = self.tile_to_surface_with_numpy(addr)
                    y = ((addr - 0x8000) // 0x10) // 0x10 
                    x = ((addr - 0x8000) // 0x10) % 0x10
                    vram_view.blit(tile, [x * 8, y * 8])
                    addr += 0x10
                    pass
                screen.blit(pygame.transform.scale_by(vram_view, 1.5), [0, 0])
                frame = pygame.surfarray.make_surface(self.ppu.frame)
                frame.set_palette([
                    [0x9b, 0xbc, 0x0f], 
                    [0x8b, 0xac, 0x0f],
                    [0x30, 0x62, 0x30], 
                    [0x0f, 0x38, 0x0f]])
                screen.blit(pygame.transform.scale_by(frame, 2), [200, 0])
                pygame.display.flip()
                

            # RENDER YOUR GAME HERE

            # flip() the display to put your work on screen
            
            clock.tick(300)  # limits FPS to 60
            pygame.display.set_caption("{}".format(clock.get_fps()))
        pygame.quit()
    # this tick is called every clock cycle (T-cycle)
    def tick(self):
        self.dma_context.tick()
        self.timer_context.tick()
        self.cpu.tick()

        # self.cpu.serial_debug()
        self.ppu.tick()
