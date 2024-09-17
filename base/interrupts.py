from base.memory import Memory
from base.bitwise_alu_operations import set_bit, reset_bit, update_bit

class InterruptContext():
    VBLANK = 0
    LCD = 1
    TIMER = 2
    SERIAL = 3
    JOYPAD = 4
    def __init__(self) -> None:     
        self.ime = False
        self.ime_enabling = False
        # interupt enable
        self.interrupt_enable = 0
        self.interrupt_flag = 0
    def isIME(self):
        return self.ime
    def setIME(self, state):
        self.ime = state

    def setEnablingIME(self, state):
        self.ime_enabling = state
    def isEnablingIME(self):
        return self.ime_enabling
    
    def isEnabled(self, type):
        return (self.interrupt_enable >> type) & 1
    def setEnabled(self, type, state):
        self.interrupt_enable = update_bit(
            self.interrupt_enable,
            type,
            state
        )

    def isRequested(self, type):
        return (self.interrupt_flag >> type) & 1
    def setRequested(self, type, state):
        self.interrupt_flag = update_bit(
            self.interrupt_flag,
            type,
            state
        )
        # print("{:08b} {:08b}".format(self.interrupt_enable, self.interrupt_flag))

class InteruptEnableRegiter(Memory):
    def __init__(self, interrupt_context: InterruptContext) -> None:
        self.context = interrupt_context
        super().__init__()
    def inside(self, addr):
        return addr == 0xFFFF
    def read(self, addr):
        return self.context.interrupt_enable
    def write(self, addr, value):
        print("IE Write {:08b}".format(value))
        self.context.interrupt_enable = value
class InteruptFlagRegister(Memory):
    def __init__(self, interrupt_context: InterruptContext) -> None:
        self.context = interrupt_context
        super().__init__()
    def inside(self, addr):
        return addr == 0xFF0F
    def read(self, addr):
        return self.context.interrupt_flag
    def write(self, addr, value):
        print("IF Write {:08b}".format(value))
        self.context.interrupt_flag = value