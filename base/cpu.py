from base.instructions import INSTRUCTIONS, PREFIXED_CB_INSTRUCTIONS
from base.register import RegisterFile
from base.memory import CartridgeMemory
from base.bus import GlobalMemory
from base.instructions import HandleInterruptInstrution

from base.interrupts import InteruptContext
    

class Cpu:
    def __init__(self, cartridge) -> None:
        self.interrupt_context = InteruptContext()
        self.is_debug = True
        self.mode = "normal"
        self.registerFile = RegisterFile()
        self.memory = GlobalMemory(cartridge, InteruptContext)
        self.debug_message = ""
        self.serial_message = ""

    # checks for interupt request and execute them if the context is sutable
    # returns True is it handeled an interupt, and False if not
    # intended to be used in every cpu tick
    def handle_interrupt(self):
        for type in range(0, 4):
            if (self.interrupt_context.isEnabled(type) and
            self.interrupt_context.isRequested(type)):
                HandleInterruptInstrution(type).execute(self)
                return True
        return False
                

    def fetch_execute_instruction(self):

        PC = self.registerFile.read("PC")
        self.registerFile.write("PC", PC + 1)
        op_code = self.memory.read(PC)

        if self.mode == "normal":
            instruction = INSTRUCTIONS[op_code]
            if op_code == 0xCB:
                self.mode = "prefixed"

        elif self.mode == "prefixed":
            instruction = PREFIXED_CB_INSTRUCTIONS[op_code]
            self.mode = "normal"
        
        # self.debug_message += "\n"
        # self.debug_message += ", ".join(self.registerFile.__repr__())

        instruction.execute(self)

        self.debug_message = "{:04X}\t {:02X}\t {}".format(PC, op_code, instruction.label)
        self.debug_message += "\n"
        self.debug_message += ", ".join(self.registerFile.__repr__())
    def serial_debug(self):
        if self.memory.read(0xFF02) & 0x80:
            # data available on the serial connection
            value = self.memory.read(0xFF01)
            self.serial_message += chr(value)
            # clear the flag
            self.memory.write(0xFF02, 0)
            print(self.serial_message)
    def tick(self):
        self.fetch_execute_instruction()
        if self.interrupt_context.isIME():
            self.handle_interrupt()
            self.interrupt_context.setEnabling(False)
        
        if self.interrupt_context.isEnabling():
            self.interrupt_context.setIME(True)
            
