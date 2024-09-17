
from memory import Memory
class DmaContext:

    def __init__(self, memory) -> None:
        self.value = 0
        self.isTransfering = False
        self.ticks = 0
    def tick():
        pass

class DMARegister(Memory):
    def __init__(self, context) -> None:
        self.context = context
        super().__init__()
    def inside(self, addr):
        return addr == 0xFF46
    def read(self, addr):
        return self.context.value
    def write(self, addr, value):
        self.context.value = value

