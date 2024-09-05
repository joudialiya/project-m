def force_d8(number):
     return number & 0xFF
def force_d16(number):
    return number & 0xFFFF
def concat_2d8(high, low):
    return ((high & 0xFF) << 8) | (low & 0xFF)
def high_low_d16(number):
    return [force_d8(number >> 8) , force_d8(number)]
def indexed_map(start, step, values=[]):
    indexed_map = {}
    index = start
    for value in values:
        indexed_map[index] = value
        index += step
    return indexed_map

class ExecutionContext:
    def __init__(self) -> None:
        pass

class RegisterFile:
    def __init__(self) -> None:
        self.dict = {
            "A": 0, "F": 0,
            "B": 0, "C": 0,
            "D": 0, "E": 0,
            "H": 0, "L": 0,
            "SP": 0,
            "PC": 0
        }
    def read(self, reg: str):
        if reg == "PC" or reg == "SP" or len(reg) == 1:
            return self.dict[reg]
        high, low = reg
        return concat_2d8(self.dict[high], self.dict[low])
    
    def write(self, reg, value):
        if reg == "PC" or reg == "SP" or len(reg) == 1:
            self.dict[reg] = value
            return
        high, low = reg
        self.dict[high], self.dict[low] = high_low_d16(value) 
    def print(self):
        for key, value in self.dict.items():
            print("{}: {} ({})".format(key, value, value))
class Memory:
    def __init__(self) -> None:
        pass
    def read(self, addr):
        raise NotImplementedError()
    def write(self, addr, value):
        raise NotImplementedError()
class CartridgeMemory(Memory):
    def __init__(self, path) -> None:
         
        with open(path,  "rb") as file:
            self.buffer = list(file.read())
            print("Loading cartridge (size: {})".format(len(self.buffer)))
        super().__init__()
    def read(self, addr):
        return self.buffer[addr]
    def write(self, addr, value):
        self.buffer[addr] = force_d8(value)

class Instruction:
    def __init__(self, opcode, cycles, callback) -> None:
        self.opcode = opcode
        self.cycles = cycles
        self.callback = callback
        pass


R8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
R16 = ["BC", "DE", "HL", "SP"]
R16STK = ["BC", "DE", "HL", "AF"]
R16MEM = ["BC", "DE", "HL+", "HL-"]
instructions = []
def callback_load(registers, memory):
    pc = registers.read("PC")
    low, high = memory.read(pc), memory.read(pc + 1)
    registers.write(pc + 2)
    

for key, value in indexed_map(0x01, 0x10, R8):
    instructions.append(Instruction(
        key,
        1,
        ))