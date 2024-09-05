from bitwise_alu_operations import *

class Memory:
    def __init__(self) -> None:
        pass
    def read(self, addr):
        raise NotImplementedError()
    def write(self, addr, value):
        raise NotImplementedError()
class CartridgeMemory(Memory):
    def __init__(self, path) -> None:
         
        with open(path,  "rb") as file:
            self.cartridge = list(file.read())
            self.vram = []
            print("Loading cartridge (size: {})".format(len(self.cartridge)))
            for i in range(0x8000, 0xA000):
                self.vram.append(0)
        super().__init__()
    def read(self, addr):
        if (addr < 0x3FFF):
            return self.cartridge[addr]
        if (addr >= 0x8000) and (addr <= 0x9FFF):
            # VRAM
            return self.vram[addr]
        return 0
    def write(self, addr, value):
        if (addr < 0x3FFF):
            self.cartridge[addr] = force_d8(value)
        if (addr >= 0x8000) and (addr <= 0x9FFF):
            # VRAM
            self.vram[addr] = force_d8(value)
        return None
