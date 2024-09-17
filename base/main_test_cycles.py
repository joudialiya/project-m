from base.instrs.instructions import *


if __name__ == "__main__":
    instrs = [{"key": key, "instr": instr} for key, instr in INSTRUCTIONS.items()]
    instrs.sort(key=lambda instr: instr["key"])
    for entry in instrs:
        print("{:02X} {} {}".format(entry["key"], entry["instr"].label, entry["instr"].getCycles()))
    print("->")
    print("->", len(get_handling_interrupt_instruction(0).ops))
    