from base.bitwise_alu_operations import *

class Memory:
    def __init__(self) -> None:
        pass
    def inside(self, addr):
        raise NotImplementedError()
    def read(self, addr):
        raise NotImplementedError()
    def write(self, addr, value):
        raise NotImplementedError()
class RAM(Memory):
    def __init__(self, start, end) -> None:
        self.start = start
        self.end = end
        self.data = []
        for i in range(0, end - start + 1):
            self.data.append(0)
        super().__init__()
    def inside(self, addr):
        return addr >= self.start and  addr <= self.end
    def read(self, addr):
        return self.data[addr - self.start]
    def write(self, addr, value):
        self.data[addr - self.start] = force_d8(value)
class IOMemory(Memory):
    def __init__(self) -> None:
        self.data = [0, 0] 
        pass
    def inside(self, addr):
        return addr == 0xFF01 or addr == 0xFF02
    def read(self, addr):
        return self.data[addr - 0xFF01]
    def write(self, addr, value):
        self.data[addr - 0xFF01] = force_d8(value)
class CartridgeMemory(Memory):
    def __init__(self, path) -> None:
         
        with open(path,  "rb") as file:
            self.cartridge = list(file.read())
            print("Loading cartridge (size: {})".format(len(self.cartridge)))
        super().__init__()
    def inside(self, addr):
        return addr < 0x8000
    def read(self, addr):
        return self.cartridge[addr - 0x0000]
    def write(self, addr, value):
        self.cartridge[addr - 0x0000] = force_d8(value)
class DummyCatrigdeMemory(Memory):
    def __init__(self):
        self.cartridge = []
        for i in range(0, 32 * 1024):
            self.cartridge.append(0x00)
    def inside(self, addr):
        return addr < 0x8000
    def read(self, addr):
        return self.cartridge[addr - 0x0000]
    def write(self, addr, value):
        self.cartridge[addr - 0x0000] = force_d8(value)
        
