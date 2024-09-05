from bitwise_alu_operations import *

class RegisterFile:
    def __init__(self) -> None:
        self.dict = {
            "A": 0, "F": 0,
            "B": 0, "C": 0,
            "D": 0, "E": 0,
            "H": 0, "L": 0,
            "SP": 0,
            "PC": 0x100
        }
    def read(self, reg: str):
        if reg == "PC" or reg == "SP" or len(reg) == 1:
            return self.dict[reg]
        high, low = reg[0], reg[1]
        return concat_2d8(self.dict[high], self.dict[low])
    
    def write(self, reg, value):
        if reg == "PC" or reg == "SP" or len(reg) == 1:
            self.dict[reg] = value
            return
        high, low = reg
        self.dict[high], self.dict[low] = high_low_d16(value) 
    def print(self):
        print("=========================")
        for key, value in self.dict.items():
            print("{}: {:02X} ({}) ({:b})".format(key, value, value, value))
        print("=========================")
