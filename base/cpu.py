from instructions import INSTRUCTIONS, PREFIXED_CB_INSTRUCTIONS
from register import RegisterFile
from memory import CartridgeMemory

class ExecutionContext:
    def __init__(self, low, high) -> None:
        self.low = low
        self.high = high
        pass

class Cpu:
    def __init__(self) -> None:
        self.mode = "normal"
        self.registerFile = RegisterFile()
        self.memory = CartridgeMemory("./roms/tetris.gb")
        self.registerFile.print()
        # Interrupt Master Enable
        self.ime = False
    def tick(self):
        PC = self.registerFile.read("PC")
        self.registerFile.write("PC", PC + 1)
        op_code = self.memory.read(PC)
        if self.mode == "normal":
            instruction = INSTRUCTIONS[op_code]
        elif self.mode == "prefixed":
            instruction = PREFIXED_CB_INSTRUCTIONS[op_code]
            self.mode = "normal"
        print("== Executing operation [{:02X}] ({}) ==".format(op_code, instruction.label))
        instruction.execute(self.registerFile, self.memory)
        self.registerFile.print()

cpu = Cpu()
#cpu.tick()


# sorted = [[key, value] for key, value in PREFIXED_CB_INSTRUCTIONS.items()]
# sorted.sort(key=lambda entry: entry[0])
# for key, value in sorted:
#     print("{:02X}\t {}".format(key, value.label))
# print(len(sorted))
