import unittest
from ..memory import DummyCatrigdeMemory
from ..cpu import Cpu
from ..bitwise_alu_operations import *
import random
class TestInstructions(unittest.TestCase):
    def test_ld_imm16_sp(self):
        memory_addr = random.randint(0xC000, 0xDFFE)
        print("Random memory addr: {:04X}".format(memory_addr))
        cartridge = DummyCatrigdeMemory()
        cartridge.write(0x100, 0x08)
        cartridge.write(0x101, memory_addr & 0xFF)
        cartridge.write(0x102, (memory_addr & 0xFF00) >> 8)
        cpu = Cpu(cartridge)
        cpu.tick()
        print(cpu.debug_message)
        sp = cpu.registerFile.read("SP")
        memory = concat_2d8(cpu.memory.read(memory_addr + 1), cpu.memory.read(memory_addr))
        
        self.assertEqual(sp, memory, "Check the memory {:04X} {:04X}".format(sp, memory))