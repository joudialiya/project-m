from base.interrupts import InterruptContext
from base.memory import Memory

class TimerContext():
    def __init__(self, interruptContext: InterruptContext) -> None:
        
        self.div = 0xABCC
        # timer counter
        self.tima = 0
        # timer modulo
        self.tma = 0
        # timer control
        self.tac = 0

        self.interrupt_context = interruptContext
        self.prev_and = 0
        self.tima_overflow = False
    def update_tima(self):
        self.tima += 1
        if self.tima > 0xFF:
            # print("TIMA OVERFLOW")
            self.tima = self.tma
            self.interrupt_context.setRequested(InterruptContext.TIMER, True)

    def tick(self):
        # if (self.tac >> 2) & 1:
        #     print("DIV: {:04X} TIMA: {:02X} TMA: {:02X} TAC: {:08b}".format(self.div, self.tima, self.tma, self.tac))
        self.div = (self.div + 1) & 0xFFFF

        div_selected_bit = None
        match self.tac & 0b11:
            case 0b00:
                div_selected_bit = (self.div >> 9) & 1
            case 0b01:
                div_selected_bit = (self.div >> 3) & 1
            case 0b10:
                div_selected_bit = (self.div >> 5) & 1
            case 0b11:
                div_selected_bit = (self.div >> 7) & 1
        
        and_result = div_selected_bit & ((self.tac >> 2) & 1)

        if self.prev_and and not and_result:
            # faling edge
            self.update_tima()

        self.prev_and = and_result

class TimerRegisters(Memory):
    def __init__(self, context: TimerContext) -> None:
        self.context = context
        super().__init__()
    def inside(self, addr):
        return addr >= 0xFF04 and addr <= 0xFF07
    def read(self, addr):
        match (addr):
            case 0xFF04:
                return self.context.div >> 8
            case 0xFF05:
                return self.context.tima
            case 0xFF06:
                return self.context.tma
            case 0xFF07:
                return self.context.tac
    def write(self, addr, value):
         match (addr):
            case 0xFF04:
                self.context.div = 0
            case 0xFF05:
                self.context.tima = value
            case 0xFF06:
                self.context.tma = value
            case 0xFF07:
                print("Tac Write {:08b}".format(value))
                self.context.tac = value