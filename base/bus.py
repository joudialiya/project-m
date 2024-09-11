from base.memory import Memory, RAM, IOMemory
from base.interrupts import InteruptEnableRegiter, InteruptFlagRegister
class GlobalMemory(Memory):
    def __init__(self, catridge, interrupt_context) -> None:
        self.wram = RAM(0xC000, 0xDFFF)
        self.hram = RAM(0xFF80, 0xFFFE)
        self.spaces = []
        self.spaces.append(catridge)
        self.spaces.append(IOMemory())
        self.spaces.append(self.wram)
        self.spaces.append(self.hram)
        self.spaces.append(InteruptEnableRegiter(interrupt_context))
        self.spaces.append(InteruptFlagRegister(interrupt_context))
        self.accesed_addr = None
        super().__init__()
    def find_space(self, addr):
        self.accesed_addr = addr
        for space in self.spaces:
            if space.inside(addr):
                # print(space, "{:04X}".format(addr))
                return space
        raise Exception("{:04X} addrs not supported".format(addr))
    def inside(self, addr):
        return True
    def read(self, addr):
        try:
            return self.find_space(addr).read(addr)
        except Exception as e:
            # print(e)
            return 0

    def write(self, addr, value):
        try:
            space = self.find_space(addr)
            space.write(addr, value)
        except Exception as e:
            # print(e)
            pass
