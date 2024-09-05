from tools import create_indexed_map
from micro_oprtations import *

class Instruction:
    def __init__(self, label) -> None:
        self.label = label
        self.ops = []
        pass
    def add(self, op):
        self.ops.append(op)
        return self
    def execute(self, registerFile, memory):
        context = None
        for op in self.ops:
            if context:
                print("== Context (HEX: {:04X}, DEC: {}) ==".format(context, context))
            else:
                print("== Context is None ==")
            if not op.proceed(registerFile, memory, context):
                break
            context = op.execute(registerFile, memory, context)


INSTRUCTIONS = {}
PREFIXED_CB_INSTRUCTIONS = {}
R8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
R16 = ["BC", "DE", "HL", "SP"]
R16STK = ["BC", "DE", "HL", "AF"]
R16MEM = ["BC", "DE", "HL+", "HL-"]
COND = ["NZ", "Z", "NC", "C"]

INSTRUCTIONS[0x00] = Instruction("NOP")

for key, value in create_indexed_map(0x01, 0x10, R16).items():
    instruction = Instruction("ld {}, imm16".format(value))
    instruction.add(LoadOperand())
    instruction.add(LoadOperand())
    instruction.add(StoreInRegister(value))
    INSTRUCTIONS[key] = instruction

for key, value in create_indexed_map(0x02, 0x10, R16MEM).items():
    instruction = (
        Instruction("ld [{}], a".format(value))
        .add(LoadFromRegistrerMemoryAddr(value))
        .add(StoreRegisterIntoAddr("A"))
    )
    if value == "HL+":
        instruction.add(IncR16Registrer("HL")) 
    elif value == "HL-":
        instruction.add(DecR16Registrer("HL")) 
    INSTRUCTIONS[key] = instruction

for key, value in create_indexed_map(0x0A, 0x10, R16MEM).items():
    instruction = Instruction("ld a, [{}]".format(value))
    instruction.add(LoadFromRegistrerMemoryAddr(value)).add(StoreInRegister("A"))
    if value == "HL+":
        instruction.add(IncR16Registrer("HL")) 
    elif value == "HL-":
        instruction.add(DecR16Registrer("HL")) 
    INSTRUCTIONS[key] = instruction

INSTRUCTIONS[0x08] = (
    Instruction("ld [imm16], sp")
    .add(LoadOperand())
    .add(LoadOperand())
    .add(StoreRegisterIntoAddr("SP"))
)

for key, value in create_indexed_map(0x03, 0x10, R16).items():
    INSTRUCTIONS[key] = Instruction("inc {}".format(value)).add(IncR16Registrer(value))

for key, value in create_indexed_map(0x0B, 0x10, R16).items():
    INSTRUCTIONS[key] = Instruction("dec {}".format(value)).add(DecR16Registrer(value))

for key, value in create_indexed_map(0x09, 0x10, R16).items():
    INSTRUCTIONS[key] = (
        Instruction("add hl, {}".format(value))
        .add(LoadOperand())
        .add(LoadOperand())
        .add(BinaryAluRegistrerOperation("HL", "add_r16"))
        .add(StoreInRegister("HL"))
    )
for key, value in create_indexed_map(0x04, 0x08, R8).items():
    instruction = Instruction("inc {}".format(value))
    if value == "(HL)":
        instruction.add(LoadFromRegistrerMemoryAddr("HL"))
        instruction.add(BinaryAluOperationWithImmediate(1, "sub"))
        instruction.add(StoreLowerByteInRegisterMemoryAddr("HL"))
    else:
        instruction.add(IncR16Registrer(value))
    INSTRUCTIONS[key] = instruction

for key, value in create_indexed_map(0x05, 0x08, R8).items():
    instruction = Instruction("dec {}".format(value))
    if value == "(HL)":
        instruction.add(LoadFromRegistrerMemoryAddr("HL"))
        instruction.add(BinaryAluOperationWithImmediate(1, "sub"))
        instruction.add(StoreLowerByteInRegisterMemoryAddr("HL"))
    else:
        instruction.add(LoadFromRegister(value))
        instruction.add(BinaryAluOperationWithImmediate(1, "sub"))
        instruction.add(StoreInRegister(value))
    INSTRUCTIONS[key] = instruction

for key, value in create_indexed_map(0x06, 0x08, R8).items():
    instruction = Instruction("ld {}, imm8".format(value))
    if value == "(HL)":
        instruction.add(LoadOperand()).add(StoreLowerByteInRegisterMemoryAddr("HL"))
    else:
        instruction.add(LoadOperand()).add(StoreInRegister(value))
    INSTRUCTIONS[key] = instruction

INSTRUCTIONS[0x07] = (
    Instruction("rlca")
    .add(LoadFromRegister("A"))
    .add(UnaryAluOperationOnContext("rlca"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0x0F] = (
    Instruction("rrca")
    .add(LoadFromRegister("A"))
    .add(UnaryAluOperationOnContext("rrca"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0x17] = (
    Instruction("rla")
    .add(LoadFromRegister("A"))
    .add(UnaryAluOperationOnContext("rla"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0x1F] = (
    Instruction("rra")
    .add(LoadFromRegister("A"))
    .add(UnaryAluOperationOnContext("rra"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0x27] = (
    Instruction("daa")
    .add(LoadFromRegister("A"))
    .add(UnaryAluOperationOnContext("daa"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0x2F] = (
    Instruction("cpl")
    .add(LoadFromRegister("A"))
    .add(UnaryAluOperationOnContext("cpl"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0x37] = (
    Instruction("scf")
    .add(UnaryAluOperationOnContext("scf"))
)
INSTRUCTIONS[0x3F] = (
    Instruction("ccf")
    .add(UnaryAluOperationOnContext("ccf"))
)
INSTRUCTIONS[0x18] = (
    Instruction("jr imm8")
    .add(LoadOperand())
    .add(BinaryAluRegistrerOperation("PC", "add_r16"))
    .add(StoreInRegister("PC"))
)
for key, value in create_indexed_map(0x20, 0x08, COND).items():
    INSTRUCTIONS[key] = (
        Instruction("jr {}, imm8".format(value))
        .add(Condition(value))
        .add(LoadOperand())
        .add(BinaryAluRegistrerOperation("PC", "add_r16", set_flags=False))
        .add(StoreInRegister("PC"))
    )
INSTRUCTIONS[0x10] = Instruction("stop")
for dest_key, dest_value in create_indexed_map(0x40, 0x08, R8).items(): 
    for src_key, src_value in create_indexed_map(dest_key, 0x01, R8).items():
        if dest_value == src_value == "(HL)":
            INSTRUCTIONS[src_key] = Instruction("HALT")
        else:
            INSTRUCTIONS[src_key] = (
                Instruction("ld {}, {}".format(dest_value, src_value))
                .add(LoadFromRegister(src_value))
                .add(StoreInRegister(dest_value))
            )


binary_arithmetic_operations = [
    "add", "adc", "sub", "sbc", "and", "xor", "or", "cp"
]
for operation_key, operation_value in create_indexed_map(
    0x80, 0x08, binary_arithmetic_operations).items():
    for register_key, register_value in create_indexed_map(
        operation_key, 0x01, R8).items():
        INSTRUCTIONS[register_key] = (
            Instruction("{} a, {}".format(operation_value, register_value))
            .add(LoadFromRegister(register_value))
            .add(BinaryAluRegistrerOperation("A", operation_value))
        )
for key, value in create_indexed_map(
    0xC6, 0x08,binary_arithmetic_operations).items():
    INSTRUCTIONS[key] = (
        Instruction("{} a, d8".format(value))
        .add(LoadOperand())
        .add(BinaryAluRegistrerOperation("A", value))
    )

for key, value in create_indexed_map(0xC0, 0x08, COND).items():
    INSTRUCTIONS[key] = (
        Instruction("ret {}".format(value))
        .add(Condition(value))
        .add(LoadFromRegistrerMemoryAddr("SP"))
        .add(IncR16Registrer("SP"))
        .add(LoadFromRegistrerMemoryAddr("SP"))
        .add(IncR16Registrer("SP"))
        .add(StoreInRegister("PC"))
        )
INSTRUCTIONS[0xC9] = (
    Instruction("ret")
    .add(LoadFromRegistrerMemoryAddr("SP"))
    .add(IncR16Registrer("SP"))
    .add(LoadFromRegistrerMemoryAddr("SP"))
    .add(IncR16Registrer("SP"))
    .add(StoreInRegister("PC"))
)
INSTRUCTIONS[0xD9] = (
    Instruction("reti")
    .add(LoadFromRegistrerMemoryAddr("SP"))
    .add(IncR16Registrer("SP"))
    .add(LoadFromRegistrerMemoryAddr("SP"))
    .add(IncR16Registrer("SP"))
    .add(StoreInRegister("PC"))
)
for key, value in create_indexed_map(0xC2, 0x08, COND).items():
    INSTRUCTIONS[key] = (
        Instruction("jp {}, d16".format(value))
        .add(Condition(value))
        .add(LoadOperand())
        .add(LoadOperand())
        .add(StoreInRegister("PC"))
        )
INSTRUCTIONS[0xC3] = (
    Instruction("jp d16")
    .add(LoadOperand())
    .add(LoadOperand())
    .add(StoreInRegister("PC"))
    )
INSTRUCTIONS[0xE9] = (
    Instruction("jp hl")
    .add(LoadFromRegister("HL"))
    .add(StoreInRegister("PC"))
    )
for key, value in create_indexed_map(0xC4, 0x08, COND).items():
    INSTRUCTIONS[key] = (
        Instruction("call {}, d16".format(value))
        .add(Condition(value))
        .add(LoadFromRegister("PC"))
        .add(StoreLowerByteInRegisterMemoryAddr("SP"))
        .add(DecR16Registrer("SP"))
        .add(StoreHigherByteInRegisterMemoryAddr("SP"))
        .add(DecR16Registrer("SP"))
        # jp
        .add(LoadOperand())
        .add(LoadOperand())
        .add(StoreInRegister("PC"))
    )
INSTRUCTIONS[0xCD] = (
    Instruction("call d16")
    .add(LoadFromRegister("PC"))
    .add(StoreLowerByteInRegisterMemoryAddr("SP"))
    .add(DecR16Registrer("SP"))
    .add(StoreHigherByteInRegisterMemoryAddr("SP"))
    .add(DecR16Registrer("SP"))
    # jp
    .add(LoadOperand())
    .add(LoadOperand())
    .add(StoreInRegister("PC"))
)
for b3 in range(0, 8):
    INSTRUCTIONS[0xC7 + (b3 << 3)] = (
        Instruction("rst {}".format(b3))
        # push 
        .add(LoadFromRegister("PC"))
        .add(StoreLowerByteInRegisterMemoryAddr("SP"))
        .add(DecR16Registrer("SP"))
        .add(StoreHigherByteInRegisterMemoryAddr("SP"))
        .add(DecR16Registrer("SP"))
        # jp
        .add(LoadImmediate(b3))
        .add(StoreInRegister("PC"))
        )

for key, value in create_indexed_map(0xC1, 0x10, R16STK).items():
    INSTRUCTIONS[key] = (
        Instruction("pop {}".format(value))
        .add(LoadFromRegistrerMemoryAddr("SP"))
        .add(IncR16Registrer("SP"))
        .add(LoadFromRegistrerMemoryAddr("SP"))
        .add(IncR16Registrer("SP"))
        .add(StoreInRegister(value))
    )
for key, value in create_indexed_map(0xC5, 0x10, R16STK).items():
    INSTRUCTIONS[key] = (
        Instruction("push {}".format(value))
        .add(LoadFromRegister(value))
        .add(StoreLowerByteInRegisterMemoryAddr("SP"))
        .add(DecR16Registrer("SP"))
        .add(StoreHigherByteInRegisterMemoryAddr("SP"))
        .add(DecR16Registrer("SP"))
    )
INSTRUCTIONS[0xCB] = (
    Instruction("$CB Prefix")
    )
INSTRUCTIONS[0xE2] = (
    Instruction("ldh [c], a")
    .add(LoadFromRegister("C"))
    .add(BinaryAluOperationWithImmediate(0xFF00, "add", set_flags=False))
    .add(StoreRegisterIntoAddr("A"))
)
INSTRUCTIONS[0xE0] = (
    Instruction("ldh [imm8], a")
    .add(LoadOperand())
    .add(BinaryAluOperationWithImmediate(0xFF00, "add", set_flags=False))
    .add(StoreRegisterIntoAddr("A"))
)
INSTRUCTIONS[0xEA] = (
    Instruction("ld [imm16], a")
    .add(LoadOperand())
    .add(LoadOperand())
    .add(StoreRegisterIntoAddr("A"))
)
INSTRUCTIONS[0xF2] = (
    Instruction("ldh a, [c]")
    .add(LoadFromRegister("C"))
    .add(BinaryAluOperationWithImmediate(0xFF00, "add"))
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0xF0] = (
    Instruction("ldh a, [imm8]")
    .add(LoadOperand())
    .add(BinaryAluOperationWithImmediate(0xFF00, "add"))
    .add(StoreRegisterIntoAddr("A"))
)
INSTRUCTIONS[0xFA] = (
    Instruction("ld a, [imm16]")
    .add(LoadOperand())
    .add(LoadOperand())
    .add(StoreInRegister("A"))
)
INSTRUCTIONS[0xE8] = (
    Instruction("add sp, imm8")
    .add(LoadOperand())
    .add(BinaryAluRegistrerOperation("SP", "add"))
    .add(StoreInRegister("SP"))
)
INSTRUCTIONS[0xF8] = (
    Instruction("add sp, imm8")
    .add(LoadOperand())
    .add(BinaryAluRegistrerOperation("SP", "add"))
    .add(StoreInRegister("HL"))
)
INSTRUCTIONS[0xF9] = (
    Instruction("ld sp, hl")
    .add(LoadFromRegister("HL"))
    .add(StoreInRegister("SP"))
)
INSTRUCTIONS[0xF3] = (
    Instruction("di")
    )
INSTRUCTIONS[0xFB] = (
    Instruction("ei")
    )

# prefixed
bitwise_operations = [
    "rlc", "rrc", "rl", "rr", "sla", "sra", "swap", "srl"
]
for operation_key, operation_value in create_indexed_map(0x00, 0x08, bitwise_operations).items():
    for register_key, register_value in create_indexed_map(operation_key, 0x01, R8).items():
        if register_key == "(HL)":
            PREFIXED_CB_INSTRUCTIONS[register_key] = (
            Instruction("{} {}".format(operation_value, register_value))
            .add(LoadFromRegistrerMemoryAddr(register_value))
            .add(UnaryAluOperationOnContext(operation_value))
            .add(StoreLowerByteInRegisterMemoryAddr(register_value))
            )
        else:
            PREFIXED_CB_INSTRUCTIONS[register_key] = (
            Instruction("{} {}".format(operation_value, register_value))
            .add(LoadFromRegister(register_value))
            .add(UnaryAluOperationOnContext(operation_value))
            .add(StoreInRegister(register_value))
    )
for key, value in create_indexed_map(0x40, 0x01, R8).items():
    for b3 in range(0, 8):
        PREFIXED_CB_INSTRUCTIONS[key + (b3 << 3)] = (
            Instruction("bit {}, {}".format(b3, value))
            .add(LoadFromRegister(value))
            .add(BinaryAluOperationWithImmediate(b3, "bit"))
            .add(StoreInRegister(value))
            )
for key, value in create_indexed_map(0x80, 0x01, R8).items():
    for b3 in range(0, 8):
        PREFIXED_CB_INSTRUCTIONS[key + (b3 << 3)] = (
            Instruction("bit {}, {}".format(b3, value))
            .add(LoadFromRegister(value))
            .add(BinaryAluOperationWithImmediate(b3, "res"))
            .add(StoreInRegister(value))
            )
for key, value in create_indexed_map(0xC0, 0x01, R8).items():
    for b3 in range(0, 8):
        PREFIXED_CB_INSTRUCTIONS[key + (b3 << 3)] = (
            Instruction("bit {}, {}".format(b3, value))
            .add(LoadFromRegister(value))
            .add(BinaryAluOperationWithImmediate(b3, "set"))
            .add(StoreInRegister(value))
            )