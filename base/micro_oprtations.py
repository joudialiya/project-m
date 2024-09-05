from bitwise_alu_operations import *
from register import RegisterFile

class MicroOp:
    def __init__(self, cycle) -> None:
        self.cycle = cycle
        pass
    def proceed(self, registerFile, memory, context):
        return True
    def execute(self, registerFile, memory, context):
        pass
class Condition(MicroOp):
    def __init__(self, condition) -> None:
        self.condition = condition
        super().__init__(0)
    def proceed(self, registerFile, memory, context):
        match self.condition:
            case "NZ":
                flags = registerFile.read("F")
                if (flags >> Z) & 1:
                    return False
                return True
            case "Z":
                flags = registerFile.read("F")
                if (flags >> Z) & 1:
                    return True
                return False
            case "NC":
                flags = registerFile.read("F")
                if (flags >> C) & 1:
                    return False
                return True
            case "C":
                flags = registerFile.read("F")
                if (flags >> Z) & 1:
                    return True
                return False
class StoreInRegister(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        print("== Store register ({}) (value: {}) ==".format(self.register, context))
        registerFile.write(self.register, context)
        return None
class StoreLowerByteInRegisterMemoryAddr(MicroOp):
    def __init__(self, registrer) -> None:
        self.register = registrer
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        addr = registerFile.read(self.register)
        memory.write(addr, force_d8(context))
        print("== Store to memory address ({}) (addr={}, value={}) =="
              .format(self.register, addr, context))
        return None
class StoreHigherByteInRegisterMemoryAddr(MicroOp):
    def __init__(self, registrer) -> None:
        self.register = registrer
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        addr = registerFile.read(self.register)
        memory.write(addr, force_d8(context >> 8))
        print("== Store to memory address ({}) (addr={}, value={}) =="
              .format(self.register, addr, context))
        return None
class StoreRegisterIntoAddr(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        value = registerFile.read(self.register)
        memory.write(context, value)
        print("== Store register into addr({}) (value: {}) ==".format(self.register, context))
        return None

class LoadImmediate(MicroOp):
    def __init__(self, imm) -> None:
        self.imm = imm
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        return self.imm
class LoadFromRegister(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        value = registerFile.read(self.register)
        return value
class LoadFromRegistrerMemoryAddr(MicroOp):
    def __init__(self, register) -> None:
        self.register = register
        super().__init__(1)
    def execute(self, registerFile: RegisterFile, memory, context):
        addr = registerFile.read(self.register)
        value = memory.read(addr)

        if context is None:
            context = value
        else:
            context = force_d8(context) | (value << 8)
        
        print("== Load from memory address ({}) (addr={}, value={}) =="
              .format(self.register, addr, value))
        return context
class LoadOperand(MicroOp):
    def __init__(self) -> None:
        super().__init__(1)
    def execute(self, registerFile: RegisterFile, memory, context):
        addr = registerFile.read("PC")
        value = memory.read(addr)
        if context is None:
            context = value
        else:
            context = force_d8(context) | (value << 8)
        registerFile.write("PC", addr + 1)
        print("== Load from memory address ({}) (addr={:02X}, value={:02X}) =="
              .format("PC", addr, value))
        return context
class IncR16Registrer(MicroOp):
    def __init__(self, registrer) -> None:
        self.registrer = registrer
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        number = registerFile.read(self.registrer)
        result, flags = add_r16(number, 1, 0)
        registerFile.write(self.registrer, result)
        registerFile.write("F", flags)
        return None
class DecR16Registrer(MicroOp):
    def __init__(self, registrer) -> None:
        self.registrer = registrer
        super().__init__(1)
    def execute(self, registerFile, memory, context):
        number = registerFile.read(self.registrer)
        result, flags = sub_r16(number, 1, 0)
        registerFile.write(self.registrer, result)
        registerFile.write("F", flags)
        return None

def getAluUnaryOperationCallback(alu):
    match alu:
        case "rl": return rl_r8
        case "rlc": return rlc_r8
        case "rr": return rr_r8
        case "rrc": return rrc_r8
        case "sla": return sla_r8
        case "sra": return sra_r8
        case "swap": return swap_r8
        case "daa": return daa_r8
        case "cpl": return cpl_r8
        case "scf": return scf
        case "ccf": return ccf
        case "srl": return srl_r8
    raise Exception("{} operation not found in the unary groupe", alu)
def getAluBinaryOperationCallback(alu):
    match alu:
        case "add_r16": return add_r16
        case "add": return add_r8
        case "sub": return sub_r8
        case "sbc": return sbc_r8
        case "or": return or_r8
        case "xor": return xor_r8
        case "and": return and_r8
        case "bit": return bit_r8
        case "set": return bit_r8
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
        super().__init__(0)

    def execute(self, registerFile, memory, context):
        callback = getAluBinaryOperationCallback(self.alu)
        result, flags = callback(context, self.imm, registerFile.read("F"))
        if self.set_flags:
            registerFile.write("F", flags)
        return result
class UnaryAluOperationOnContext(MicroOp):
    def __init__(self, alu, set_flags=True) -> None:
        self.alu = alu
        self.set_flags = set_flags
        super().__init__(0)

    def execute(self, registerFile, memory, context):
        callback = getAluUnaryOperationCallback(self.alu)
        result, flags = callback(context, registerFile.read("F"))
        if self.set_flags:
            registerFile.write("F", flags)
        return result
class BinaryAluRegistrerOperation(MicroOp):
    def __init__(self, registrer, alu, set_flags=True) -> None:
        self.register = registrer
        self.alu = alu
        self.set_flags = set_flags
        super().__init__(0)

    def execute(self, registerFile, memory, context):
        callback = getAluBinaryOperationCallback(self.alu)
        register = registerFile.read(self.register)
        result, flags = callback(register, context, registerFile.read("F"))
        if self.set_flags:
            registerFile.write("F", flags)
        return result