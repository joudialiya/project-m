from base.bitwise_alu_operations import *
from base.register import RegisterFile

class MicroOp:
    def isAccessingMemory(self):
        return False
    def isUsingIDU(self):
        return False
    def proceed(self, cpu, context):
        return True
    def execute(self, cpu, context):
        pass
class ExtraCycle(MicroOp):
    def isAccessingMemory(self):
        return True
    def isUsingIDU(self):
        return True
    def execute(self, cpu, context):
        return context
class Halt(MicroOp):
    def execute(self, cpu, context):
        # print("Halted")
        cpu.isHalted = True
        return context
class EnableDisableIME(MicroOp):
    def __init__(self, state, with_delay=False) -> None:
        self.state = state
        self.with_delay = with_delay
    def proceed(self, cpu, context):
        return True
    def execute(self, cpu, context):
        if self.state:
            if self.with_delay:
                cpu.interrupt_context.setEnablingIME(True)
            else:
                cpu.interrupt_context.setIME(True)
        else:
            cpu.interrupt_context.setIME(False)
        return context
class Condition(MicroOp):
    def __init__(self, condition) -> None:
        self.condition = condition
    def execute(self, cpu, context):
        return context
    def proceed(self, cpu, context):
        flags = cpu.registerFile.read("F")
        match self.condition:
            case "NZ":
                return not ((flags >> Z) & 1)
            case "Z":
                return (flags >> Z) & 1
            case "NC":
                return not ((flags >> C) & 1)
            case "C":
                return (flags >> C) & 1
class StoreInRegister(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
    def execute(self, cpu, context):
        cpu.registerFile.write(self.register, context)
        return context

class StoreLowerByteInRegisterMemoryAddr(MicroOp):
    def __init__(self, registrer) -> None:
        self.register = registrer
    def isAccessingMemory(self):
        return True
    def execute(self, cpu, context):
        addr = cpu.registerFile.read(self.register)
        cpu.memory.write(addr, force_d8(context))
        # print("{:02X} in {:04X}".format(force_d8(context), addr))
        return context
class StoreHigherByteInRegisterMemoryAddr(MicroOp):
    def __init__(self, registrer) -> None:
        self.register = registrer
    def isAccessingMemory(self):
        return True
    def execute(self, cpu, context):
        addr = cpu.registerFile.read(self.register)
        cpu.memory.write(addr, force_d8(context >> 8))
        # print("{:02X}".format(force_d8(context >> 8)))
        return context
class StoreRegisterIntoAddr(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
    def isAccessingMemory(self):
        return True
    def execute(self, cpu, context):
        value = cpu.registerFile.read(self.register)
        cpu.memory.write(context, value)
        return None

class LoadImmediate(MicroOp):
    def __init__(self, imm) -> None:
        self.imm = imm
    def execute(self, cpu, context):
        return self.imm
class LoadFromRegister(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
    def execute(self, cpu, context):
        value = cpu.registerFile.read(self.register)
        return value
class LoadFromRegisterMemoryAddr(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
    def isAccessingMemory(self):
        return True
    def execute(self, cpu, context):
        addr = cpu.registerFile.read(self.register)
        value = cpu.memory.read(addr)
        # print("Load from {:04X} value {:02X}".format(addr, value))
        return value
class LoadOperand(MicroOp):
    def isAccessingMemory(self):
        return True
    def isUsingIDU(self):
        return True
    def execute(self, cpu, context):
        addr = cpu.registerFile.read("PC")
        value = cpu.memory.read(addr)
        # print("addr {:04X} value {:02X}".format(addr, value))
        context = force_d8(value)
        cpu.registerFile.write("PC", addr + 1)
        return context

class IncR16Registrer(MicroOp):
    def __init__(self, registrer) -> None:
        self.registrer = registrer
    def execute(self, cpu, context):
        number = cpu.registerFile.read(self.registrer)
        result, flags = add_r16(number, 1, 0)
        cpu.registerFile.write(self.registrer, result)
        return context
class DecR16Registrer(MicroOp):
    def __init__(self, registrer) -> None:
        self.registrer = registrer
    def execute(self, cpu, context):
        number = cpu.registerFile.read(self.registrer)
        result, flags = sub_r16(number, 1, 0)
        cpu.registerFile.write(self.registrer, result)
        return context


def getAluUnaryOperationCallback(alu):
    match alu:
        case "rl": return rl_r8
        case "rla": return rla_r8
        case "rlc": return rlc_r8
        case "rlca": return rlca_r8
        case "rr": return rr_r8
        case "rra": return rra_r8
        case "rrc": return rrc_r8
        case "sla": return sla_r8
        case "sra": return sra_r8
        case "swap": return swap_r8
        case "daa": return daa_r8
        case "cpl": return cpl_r8
        case "scf": return scf
        case "ccf": return ccf
        case "srl": return srl_r8
        case "rrca": return rrca_r8
        case "signed": return lambda number, flags: [to_signed_d8(number), flags]
        case "inc": return inc_r8
        case "dec": return dec_r8
    raise Exception("{} operation not found in the unary groupe", alu)
def getAluBinaryOperationCallback(alu):
    match alu:
        case "add_r16": return add_r16
        case "add_sp": return add_sp

        case "add": return add_r8
        case "adc": return adc_r8
        
        case "sub": return sub_r8
        case "sbc": return sbc_r8
        case "cp": return cp_r8

        case "or": return or_r8
        case "xor": return xor_r8
        case "and": return and_r8

        case "bit": return bit_r8
        case "set": return set_r8
        case "res": return res_r8
          
    raise Exception("{} operation not found in the binary groupe", alu)

# These micro operation sets the context to the result of the alu operation
# and sets the flags 2, so if u need to save the result u will need to use one
# of the stare micro operations
class BinaryAluOperationWithImmediate(MicroOp):
    def __init__(self, imm, alu, set_flags=True) -> None:
        self.imm = imm
        self.alu = alu
        self.set_flags = set_flags

    def execute(self, cpu, context):
        callback = getAluBinaryOperationCallback(self.alu)
        result, flags = callback(context, self.imm, cpu.registerFile.read("F"))
        if self.set_flags:
            cpu.registerFile.write("F", flags)
        return result
class UnaryAluOperationOnContext(MicroOp):
    def __init__(self, alu, set_flags=True) -> None:
        self.alu = alu
        self.set_flags = set_flags

    def execute(self, cpu, context):
        callback = getAluUnaryOperationCallback(self.alu)
        result, flags = callback(context, cpu.registerFile.read("F"))
        if self.set_flags:
            cpu.registerFile.write("F", flags)
        return result
class BinaryAluRegistrerOperation(MicroOp):
    def __init__(self, registrer, alu, set_flags=True) -> None:
        self.register = registrer
        self.alu = alu
        self.set_flags = set_flags

    def execute(self, cpu, context):
        callback = getAluBinaryOperationCallback(self.alu)
        register = cpu.registerFile.read(self.register)
        result, flags = callback(register, context, cpu.registerFile.read("F"))
        if self.set_flags:
            cpu.registerFile.write("F", flags)
        return result