from base.bitwise_alu_operations import *

class RegisterFile:
    def __init__(self) -> None:
        self.dict = {
            "A": 0x01, "F": 0xB0,
            "B": 0x00, "C": 0x13,
            "D": 0x00, "E": 0xD8,
            "H": 0x01, "L": 0x4D,
            "SP": 0xFFFE,
            "PC": 0x0100,
            "W": 0, "Z": 0
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

        high, low = reg[0], reg[1]
        if reg[1] == "F":
            self.dict[high], self.dict[low] = high_low_d16(value)[0], value & 0xF0 
        else:
            self.dict[high], self.dict[low] = high_low_d16(value) 
    def __repr__(self):
        strings = ["{}: ".format(key) +
                   ("{:08b}" if key == "F" 
                    else "{:02X}" if len(key) == 1 
                    else "{:04X}")
                    .format(value)
                   for key, value in self.dict.items()]
        return strings

