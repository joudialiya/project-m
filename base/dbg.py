from base.cpu import CyceledCpu
from base.emu import Emu

class EmuDebuger:
    def __init__(self, emu) -> None:
        self.emu: Emu = emu
        self.cpu: CyceledCpu = emu.cpu
        self.mode = "next"
        self.target_addr = None
        self.command = None
        self.nop_inst_count = 0

    def tick(self):
        match self.mode:
            case "end":
                print("LAST INSTRUCTION")
                print(self.cpu.debug_message)
                print("SERIAL MESSAGE")
                print(self.cpu.serial_message)
                input("(end) >")

            case "nop":
                self.command = input("(nop) > ")
                self.mode = "command"

            case "next":
                self.emu_tick()
                self.debug_message = "{:04X}\t {:02X}\t {}".format(
                    self.emu.cpu.current_pc,
                    self.emu.cpu.current_opcode,
                    self.emu.cpu.current_instruction.label)
                self.debug_message += "\n"
                self.debug_message += ", ".join(self.emu.cpu.registerFile.__repr__())
                print(self.debug_message)
                self.mode = "command"

            case "skip":
                if self.target_addr == self.cpu.current_pc:
                    self.skip_repeat -= 1
                    print("\tSKIP REPEAT: {}".format(self.skip_repeat))

                if self.skip_repeat == 0:
                    print(self.cpu.debug_message)
                    self.mode = "command"
                else:
                    self.emu_tick(False)
    
            case "command":
                self.command = input("> ")
                self.execute_command()
    def emu_tick(self, vebose=True): 
        pc = self.cpu.current_pc
        


        self.emu.step_by_instruction()
        if vebose:
            print(self.cpu.debug_message)
        if not self.emu.cpu.isHalted:
            if self.cpu.memory.read(pc) == 0:
                self.nop_inst_count += 1
            else:
                self.nop_inst_count = 0
            if self.nop_inst_count > 5:
                self.mode = "end"
                
            if self.cpu.current_pc == pc:
                print ("END {:04X}".format(pc))
                self.mode = "end"
    def execute_command(self):
        if len(self.command) > 0 :
            match self.command[0]:
                case "m":
                    try:
                        addr = int(self.command.split(" ")[1], 16)
                        print("Addr {:04X}: {:02X}".format(addr, self.cpu.memory.read(addr)))
                    except Exception as e:
                        print(e)
                    finally:
                        self.mode = "nop"
                case "s":
                    try:
                        command_fragments = self.command.split(" ")
                        self.target_addr = int(command_fragments[1], 16)
                        if len(command_fragments) > 2:
                            self.skip_repeat = int(command_fragments[2])
                        else:
                            self.skip_repeat = 1
                        self.mode = "skip"
                        print("SKIP TO: {:04X} {} TIME(S)".format(
                            self.target_addr,
                            self.skip_repeat))
                    except Exception as e:
                        print(e)
                        self.mode = "nop"
                case _:
                    self.mode = "nop"
                
        else:
            self.mode = "next"
