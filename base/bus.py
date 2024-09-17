from base.memory import Memory, RAM, IOMemory
from base.interrupts import InteruptEnableRegiter, InteruptFlagRegister
from base.timer import TimerRegisters
from base.ppu import *
class GlobalMemory(Memory):
    def __init__(self) -> None:
        self.spaces = []
        # vram
        self.indexed_spaces = []
        super().__init__()
    def find_space(self, addr):
        self.accesed_addr = addr
        for space in self.spaces:
            if space.inside(addr):
                # print(space, "{:04X}".format(addr))
                return space
    def index_spaces(self):
        for addr in range(0, 0x10000):
            space = self.find_space(addr)
            self.indexed_spaces.append(space)
            
    def inside(self, addr):
        return True
    def read(self, addr):
        try:
            return self.indexed_spaces[addr].read(addr)
        except Exception as e:
            # print(e)
            return 0
    def write(self, addr, value):
        try:
            self.indexed_spaces[addr].write(addr, value)
        except Exception as e:
            print("{:04X} addrs not supported".format(addr))
            pass
