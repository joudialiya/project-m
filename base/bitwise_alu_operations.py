def force_d8(number):
     return number & 0xFF
def force_d16(number):
    return number & 0xFFFF
def concat_2d8(high, low):
    return ((high & 0xFF) << 8) | (low & 0xFF)
def high_low_d16(number):
    return [force_d8(number >> 8) , force_d8(number)]
def to_signed_d8(number):
    if (number >> 7) & 1:
        # meaning its a negative number
        return number - 0x100
    return number
# ----------------------------------
def set_bit(a, index):
    return a | (1 << index)
def reset_bit(a, index):
    return a & ~(1 << index)
# ----------------------------------
Z = 7
N = 6
H = 5
C = 4
def set_zero(a):
    return set_bit(a, Z)
def set_carry(a):
    return set_bit(a, C)
def set_aux_carry(a):
    return set_bit(a, H)
def set_sub(a):
    return set_bit(a, N)
# ------------------- alu operations
# returns [result, flags: int number]
# ---- helper functions 
def calculate_add_flags_d8(number):
    flags = 0
    if number == 0:
        flags = set_zero(flags)
    if number > 0xFF:
        flags = set_carry(flags)
    return flags
def calculate_add_flags_d16(number):
    flags = 0
    if number == 0:
        flags = set_zero(flags)
    if number > 0xFFFF:
        flags = set_carry(flags)
    return flags
# ---------------------
def add_r8(a, b, flags, with_carry=False):
    result = a + b
    if with_carry:
        result += ((flags >> C) & 1)
    return [force_d8(result), calculate_add_flags_d8(result)]
def add_r16(a, b, flags, with_carry=False):
    result = a + b
    if with_carry:
        result += ((flags >> C) & 1)
    return [force_d16(result), calculate_add_flags_d16(result)]
def sub_r8(a, b, flags):
    result = a - b
    flags = 0
    flags = set_sub(flags)
    if result == 0:
        flags = set_zero(flags)
    if b > a:
        flags = set_carry(flags)
    return [force_d8(result), flags]
def sub_r16(a, b, flags):
    result = a - b
    flags = 0
    flags = set_sub(flags)
    if result == 0:
        flags = set_zero(flags)
    if b > a:
        flags = set_carry(flags)
    return [force_d16(result), flags]
def sbc_r8(a, b, flags):
    b_plus_carry = b + ((flags >> C) & 1) 
    result = a - b_plus_carry
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    if b_plus_carry > a:
        flags = set_carry(flags)
    return [force_d8(result), flags]
def and_r8(a, b, flags=0):
    result = a & b
    flags = 0
    if result == 0:
        flags = set_zero()
    return [force_d8(result), flags]
def or_r8(a, b, flas=0):
    result = a | b
    flags = 0
    if result == 0:
        flags = set_zero()
    return [force_d8(result), flags]
def xor_r8(a, b, flags=0):
    result = (a & ~b) | (~a & b)
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    return [force_d8(result), flags]
def rl_r8(number, flags):
    result = number << 1
    if (flags >> C) & 1:
        result |= 1
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    if result >> 8 == 1:
        flags = set_carry(flags)
    return [force_d8(result), flags]   
def rr_r8(number, flags):
    result = number >> 1
    if (flags >> C) & 1:
        result |= 0x80
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    if (number & 1) == 1:
        set_carry(flags)
    return [force_d8(result), flags]
def rlc_r8(number, flags):
    result = ((number & 0x80) >> 7) | (number << 1)
    flags = 0
    if result == 0:
        set_zero(flags) 
    if number & 0x80:
        set_carry(flags)
    return [result, flags]
def rrc_r8(number, flags):
    result = ((number & 1) << 7) | (number >> 1)
    flags = 0
    if result == 0:
        set_zero(flags) 
    if number & 1:
        set_carry(flags)
    return [result, flags]
def sla_r8(number, flags):
    result = number << 1
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    if result >> 8 == 1:
        flags = set_carry(flags)
    return [force_d8(result), flags] 
def sra_r8(number, flags):
    result = (number & 0x80) | (number >> 1)
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    if number & 1:
        flags = set_carry(flags)
    return [force_d8(result), flags] 
def srl_r8(number, flags):
    result = number >> 1
    flags = 0
    if result == 0:
        flags = set_zero(flags)
    if number & 1:
        flags = set_carry(flags)
    return [force_d8(result), flags] 
def swap_r8(number, flags):
    result = (force_d8(number & 0x0F) << 4) | (force_d8(number & 0xF0) >> 4)
    return [result, 0]
def daa_r8(number, flags):
    if (flags >> N) & 1:
        if (flags >> H) & 1:
            number = (number - 6) & 0xff
        
        if (flags >> C) & 1:
            number = (number - 0x60) & 0xff
    else:
        if ((flags >> H) & 1) or ((number & 0xf) > 9):
            number += 0x06
        if ((flags >> C) & 1) or (number > 0x9f):
            number += 0x60
    flags = 0
    if (number > 0xff):
        flags = set_carry(flags)
    number &= 0xff
    if number is 0:
        flags = set_zero(flags)
    return [number, flags]
def cpl_r8(number, flags):
    flags = 0
    flags = set_aux_carry(flags)
    flags = set_sub(flags)
    return [~number, flags]
def scf(number, flags):
    flags = 0
    flags = set_carry(flags)
    return [None, flags]
def ccf(number, flags):
    if (flags >> C) & 1:
        flags = reset_bit(flags, C)
    else:
        flags = set_carry(flags)
    return [None, flags]
def bit_r8(number, bit, flags):
    flags = 0
    flags = set_aux_carry(flags)
    if (number >> bit) & 1:
        pass
    else:
        flags = set_zero(flags)
    return [None, flags]
def set_r8(number, bit, flags):
    result = set_bit(number, bit)
    return [result, flags]
def res_r8(number, bit, flags):
    result = reset_bit(number, bit)
    return [result, flags]   
def dec_r8(number, flags):
    result = number - 1
    flags = 0
    
# ------------------- alu operations