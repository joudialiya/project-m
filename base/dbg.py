class MemoryCapture():
    def __init__(self, cpu) -> None:
        self.cpu = cpu
        pass
    def perform(self, addr):
        self.cpu.memory_access_addr = addr
        print("+ Addr is {:04X}".format(self.memory_access_addr))