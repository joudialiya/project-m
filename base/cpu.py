from base.instrs.instructions import *
from base.instrs.mop import MicroOp
from base.register import RegisterFile
from base.memory import CartridgeMemory
from base.bus import GlobalMemory
from base.interrupts import InterruptContext
from base.timer import TimerContext
    
class CpuState():
    FEATCHING = 0
    EXECUTING = 1
    STOP = 2
    HALT = 3
    HANDLING_INTERUPTS = 4
class FeachingMode():
    NORMAL = 0
    PREFIXED = 1
class Cpu:
    def __init__(self, cartridge) -> None:
        self.interrupt_context = InterruptContext()
        self.is_debug = True
        self.mode = "normal"

        self.registerFile = RegisterFile()
        self.memory = GlobalMemory(cartridge, InterruptContext)
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
        # fetch 
        self.registerFile.write("PC", PC + 1)
        self.current_opcode = self.memory.read(PC)

        if self.mode == "normal":
            instruction = INSTRUCTIONS[self.current_opcode]
            if self.current_opcode == 0xCB:
                self.mode = "prefixed"

        elif self.mode == "prefixed":
            instruction = PREFIXED_CB_INSTRUCTIONS[self.current_opcode]
            self.mode = "normal"
        
        # self.debug_message += "\n"
        # self.debug_message += ", ".join(self.registerFile.__repr__())

        instruction.execute(self)

        self.debug_message = "{:04X}\t {:02X}\t {}".format(PC, self.current_opcode, instruction.label)
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
            self.interrupt_context.setEnablingIME(False)
        
        if self.interrupt_context.isEnablingIME():
            self.interrupt_context.setIME(True)

        
class CyceledCpu:
    def __init__(
            self, 
            timer_context: TimerContext,
            interrupt_context: InterruptContext,
            memory
        ) -> None:
        self.timer_context = timer_context
        self.interrupt_context = interrupt_context
        self.memory = memory
        

        self.registerFile = RegisterFile()

        self.debug_message = ""
        self.serial_message = ""
        
        self.isHalted = False
        
        self.feaching_mode = FeachingMode.NORMAL
        self.state = CpuState.FEATCHING
        self.t_ticks = 0

        self.current_pc = 0
        self.current_opcode = 0
        self.current_instruction: Instruction = None
        self.index_of_micro_operation = 0
        self.current_context = None
        self.passed_by_feaching = False


    def serial_debug(self):
        if self.memory.read(0xFF02) & 0x80:
            print("SERIAL ADD")
            # data available on the serial connection
            value = self.memory.read(0xFF01)
            self.serial_message += chr(value)
            # clear the flag
            self.memory.write(0xFF02, 0)
            print("SERIAL OUTPUT:", self.serial_message)
    def check_for_interrupt(self):
        for type in range(0, 5):
            if self.interrupt_context.isEnabled(type) and self.interrupt_context.isRequested(type):
                return type 
        return None

    def tick(self):
        
        self.passed_by_feaching = False
        # we do non out of a machine tick wtich is 4 clock ticks
        # print("MODE: {} Accumulative tick count: {}".format(self.state, self.t_ticks))
        # print(self.debug_message)
        if self.t_ticks < 4:
            self.t_ticks += 1
            return
        self.t_ticks = 0
        # ------------------------------------------------------------
        if self.interrupt_context.isEnablingIME():
            print("Enable IME")
            self.interrupt_context.setEnablingIME(False)
            self.interrupt_context.setIME(True)
        
        isCurrentCycleAccessingMemory = False
        isCurrentCycleUsingIDU = False
        while(True):
            # print("IN THE SAME CYCLE")
            match self.state:
                case CpuState.HANDLING_INTERUPTS:
                    interupt_type = self.check_for_interrupt()
                    if interupt_type is not None:
                        # print("ACK")
                        # exit the halt state
                        self.isHalted = False
                        # if the master interrupt is enable too then we handle the interrupt
                        if self.interrupt_context.isIME():
                            print("Handle")
                            self.interrupt_context.setIME(False)
                            self.interrupt_context.setRequested(interupt_type, False)
                            self.current_instruction = get_handling_interrupt_instruction(interupt_type)

                            self.start_of_instruction = True
                            self.index_of_micro_operation = 0
                            self.current_context = None
                            self.state = CpuState.EXECUTING
                            break
                    if self.isHalted:
                        break
                    else:
                        self.state = CpuState.FEATCHING

                case CpuState.FEATCHING:

                    # cant fetch if the curent cycle read the memory, or used the IDU
                    if (isCurrentCycleAccessingMemory or isCurrentCycleUsingIDU):
                        # entre new cycle by return from the loop
                        break

                    # get program counter
                    self.current_pc = self.registerFile.read("PC")
                    # read next opcode
                    self.current_opcode = self.memory.read(self.current_pc)

                    # skip the incrementingon the halt 
                    # if self.current_opcode != 0x76:
                        # increment the program counter
                    self.registerFile.write("PC", self.current_pc + 1)
                    
                    match self.feaching_mode:
                        case FeachingMode.NORMAL:
                            self.current_instruction = INSTRUCTIONS[self.current_opcode]
                            if self.current_opcode == 0xCB:
                                self.feaching_mode = FeachingMode.PREFIXED
                        case FeachingMode.PREFIXED:
                            self.current_instruction = PREFIXED_CB_INSTRUCTIONS[self.current_opcode]
                            self.feaching_mode = FeachingMode.NORMAL
                    # reset the index of the instruction micro operation

                    self.index_of_micro_operation = 0
                    self.current_context = None
                    self.state = CpuState.EXECUTING

                    isCurrentCycleAccessingMemory = True
                    isCurrentCycleUsingIDU = True

                    # fething always ends the cycle
                    # print("BREAK ON FEATHING")

                    # -----------------------------------------
                    # self.debug_message = "{:04X}\t {:02X}\t {}".format(
                    #     self.current_pc,
                    #     self.current_opcode,
                    #     self.current_instruction.label)
                    # self.debug_message += "\n"
                    # self.debug_message += ", ".join(self.registerFile.__repr__())
                    # print(self.debug_message)
                    # -----------------------------------------
                    self.passed_by_feaching = True
                    break

                case CpuState.EXECUTING:
                    # we ve executed all of the micro operations
                    if self.index_of_micro_operation >= len(self.current_instruction.ops):
                        self.state = CpuState.HANDLING_INTERUPTS
                        continue
                    op: MicroOp = self.current_instruction.ops[self.index_of_micro_operation]

                    # if this is true -> skip to the next cycle
                    if ((op.isAccessingMemory() and isCurrentCycleAccessingMemory) 
                        or
                        (op.isUsingIDU() and isCurrentCycleUsingIDU)):
                        # entre new cycle by return from the loop
                        break
                    # print("Executing", op.__class__)

                    if op.proceed(self, self.current_context):
                        try:
                            self.current_context = op.execute(self, self.current_context)
                        except Exception as e:
                            print(self.debug_message)
                            print("OP", op.__class__)
                            print(e)
                            exit()
                        
                        self.index_of_micro_operation += 1

                        # -----------------------------------------
                        # Update the flags the determin if the next op
                        # can be executed on the same cycle 
                        if op.isAccessingMemory():
                            isCurrentCycleAccessingMemory = True
                        if op.isUsingIDU():
                            isCurrentCycleUsingIDU = True
                        # -----------------------------------------

                    else:
                        self.state = CpuState.HANDLING_INTERUPTS