from base.instrs.instructions import *
from base.instrs.mop import MicroOp
from base.register import RegisterFile
from base.memory import CartridgeMemory
from base.bus import GlobalMemory
from base.interrupts import InterruptContext
from base.timer import TimerContext
from enum import Enum 
import cython
    
CPU_STATE_FEATCHING: cython.int = 0
CPU_STATE_EXECUTING: cython.int = 1
STOP: cython.int = 2
HALT: cython.int = 3
CPU_STATE_HANDLING_INTERUPTS: cython.int = 4

FEACHING_MODE_NORMAL: cython.int = 0
FEACHING_MODE_PREFIXED: cython.int = 1
        
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
        
        self.feaching_mode: cython.int = FEACHING_MODE_NORMAL
        self.state: cython.int = CPU_STATE_FEATCHING
        self.t_ticks: cython.int = 0

        self.current_pc: cython.int = 0
        self.current_opcode: cython.int = 0
        self.current_instruction: Instruction
        self.index_of_micro_operation = 0
        self.current_context: cython.int = None
        self.passed_by_feaching = False

    def set_debug_message(self):
        self.debug_message = "{:04X}\t {:02X}\t {}".format(
            self.current_pc,
            self.current_opcode,
            self.current_instruction.label)
        self.debug_message += "\n"
        self.debug_message += ", ".join(self.registerFile.__repr__())
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
            self.interrupt_context.setEnablingIME(False)
            self.interrupt_context.setIME(True)
        
        isCurrentCycleAccessingMemory = False
        isCurrentCycleUsingIDU = False
        while(True):
            # print("IN THE SAME CYCLE")
            if self.state == CPU_STATE_HANDLING_INTERUPTS:
                interupt_type = self.check_for_interrupt()
                if interupt_type is not None:
                    # print("ACK")
                    # exit the halt state
                    self.isHalted = False
                    # if the master interrupt is enable too then we handle the interrupt
                    if self.interrupt_context.isIME():
                        # print("Handle", interupt_type)
                        self.interrupt_context.setIME(False)
                        self.interrupt_context.setRequested(interupt_type, False)
                        self.current_instruction = get_handling_interrupt_instruction(interupt_type)

                        self.start_of_instruction = True
                        self.index_of_micro_operation = 0
                        self.current_context = None
                        self.state = CPU_STATE_EXECUTING
                        break
                if self.isHalted:
                    # -----------------------------------------
                    # self.debug_message = "{:04X}\t {:02X}\t {}".format(
                    #     self.current_pc,
                    #     self.current_opcode,
                    #     self.current_instruction.label)
                    # self.debug_message += "\n"
                    # self.debug_message += ", ".join(self.registerFile.__repr__())
                    # print(self.debug_message)
                    # -----------------------------------------
                    break
                else:
                    self.state = CPU_STATE_FEATCHING

            elif self.state == CPU_STATE_FEATCHING:
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
                
                if self.feaching_mode == FEACHING_MODE_NORMAL:
                    self.current_instruction = INSTRUCTIONS[self.current_opcode]
                    if self.current_opcode == 0xCB:
                        self.feaching_mode = FEACHING_MODE_PREFIXED
                elif self.feaching_mode == FEACHING_MODE_PREFIXED:
                    self.current_instruction = PREFIXED_CB_INSTRUCTIONS[self.current_opcode]
                    self.feaching_mode = FEACHING_MODE_NORMAL
                # reset the index of the instruction micro operation

                self.index_of_micro_operation = 0
                self.current_context = None
                self.state = CPU_STATE_EXECUTING

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

            elif self.state == CPU_STATE_EXECUTING:
                # we ve executed all of the micro operations
                if self.index_of_micro_operation >= len(self.current_instruction.ops):
                    self.state = CPU_STATE_HANDLING_INTERUPTS
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
                        # self.set_debug_message()
                        print(self.debug_message)
                        print("OP", op.__class__, "OPCODE", "{:02X}".format(self.current_opcode), "PC", "{:04X}".format(self.current_pc))
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
                    self.state = CPU_STATE_HANDLING_INTERUPTS