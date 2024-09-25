
from base.memory import Memory
class DmaContext:
    def __init__(self, memory) -> None:
        self.value = 0
        self.memory = memory
        self.is_transfering = False
        self.ticks = 0
        self.index = 0

    def start(self, value):
        self.value = value
        self.index = 0
        self.ticks = 0
        self.is_transfering = True
    def tick(self):
        if self.is_transfering:
            
            self.ticks += 0
            if self.ticks % 4 == 0:
                print("Copying", ((self.value << 8) & 0xFF) + self.index)
                value = self.memory.read(((self.value << 8) & 0xFF) + self.index)
                self.memory.write(0xFE00 + self.index, value)
                self.index += 1
                if self.index == 160:
                    self.is_transfering = False

class DMARegister(Memory):
    def __init__(self, context) -> None:
        self.context = context
        super().__init__()
    def inside(self, addr):
        return addr == 0xFF46
    def read(self, addr):
        return self.context.value
    def write(self, addr, value):
        self.context.start(value)

