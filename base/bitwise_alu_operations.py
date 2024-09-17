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
def update_bit(flags, bit, condition):
    if condition:
        return set_bit(flags, bit)
    else:
        return reset_bit(flags, bit)
# ------------------- alu operations
# returns [result, flags: int number]
# ---- helper functions
def add_r16(a, b, flags):
    result = a + b
    result = force_d16(result)

    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, ((a & 0x0FFF) + (b & 0x0FFF)) > 0x0FFF)
    flags = update_bit(flags, C, (a + b) > 0xFFFF)
    
    return [result, flags]
def add_r16_lb(a, b, flags):
    result = a + b
    result = force_d8(result)

    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, ((a & 0x0F) + (b & 0x0F)) > 0x0F)
    flags = update_bit(flags, C, (a + b) > 0xFF)
    
    return [result, flags]
def add_r16_hb(a, b, flags):
    carry = (flags >> C) & 1
    result = a + b + carry
    result = force_d8(result)

    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, ((a & 0x0F) + (b & 0x0F) + carry) > 0x0F)
    flags = update_bit(flags, C, (a + b + carry) > 0xFF)
    
    return [result, flags]
def add_sp(a, b, flags):
    result = a + b
    result = force_d16(result)

    flags = update_bit(flags, Z, False)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, ((a & 0x000F) + (b & 0x000F)) > 0x000F)
    flags = update_bit(flags, C, ((a & 0x00FF) + (b & 0x00FF)) > 0x00FF)
    
    return [result, flags]
def sub_r16(a, b, flags):
    result = a - b
    result = force_d16(result)
    flags = 0
    flags = set_sub(flags)
    if result == 0:
        flags = set_zero(flags)
    if b > a:
        flags = set_carry(flags)
    return [result, flags]
# ---------------------
def add_r8(a, b, flags):
    result = a + b
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, ((a & 0xF) + (b & 0xF)) > 0xF)
    flags = update_bit(flags, C, (a + b) > 0xFF)

    return [result, flags]
def adc_r8(a, b, flags):
    
    carry = (flags >> C) & 1

    result = a + b + carry
    result = force_d8(result)
   
    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, ((a & 0xF) + (b & 0xF) + carry) > 0xF)
    flags = update_bit(flags, C, (a + b + carry) > 0xFF)

    return [result, flags]
def sub_r8(a, b, flags):
    result = a - b
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, True)
    flags = update_bit(flags, H, (b & 0xF) > (a & 0xF))
    flags = update_bit(flags, C, b > a)

    return [result, flags]
def cp_r8(a, b, flags):
    result = a - b
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, True)
    flags = update_bit(flags, H, (b & 0xF) > (a & 0xF))
    flags = update_bit(flags, C, b > a)

    return [a, flags]
def sbc_r8(a, b, flags):
    
    carry = (flags >> C) & 1 

    result = a - b - carry
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, True)
    flags = update_bit(flags, H, (b & 0xF) + carry > (a & 0xF))
    flags = update_bit(flags, C, (b + carry) > a)

    return [result, flags]

def and_r8(a, b, flags=0):
    result = a & b
    
    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, True)
    flags = update_bit(flags, C, False)

    return [result, flags]
def or_r8(a, b, flags=0):
    result = a | b

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, False)
    return [result, flags]
def xor_r8(a, b, flags=0):
    result = (a & ~b) | (~a & b)
    result = force_d8(result)
    
    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, False)
    return [result, flags]

def rl_r8(number, flags):
    carry = (flags >> C) & 1
    result = (number << 1) | carry

    result = force_d8(result)
    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, number & 0x80)

    return [result, flags]   
def rla_r8(number, flags):
    result, flags = rl_r8(number, flags)
    flags = update_bit(flags, Z, False)
    return [result, flags]
def rlc_r8(number, flags):
    result = ((number & 0x80) >> 7) | (number << 1)
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, number & 0x80)

    return [result, flags]
def rlca_r8(number, flags):
    result, flags = rlc_r8(number, flags)
    flags = update_bit(flags, Z, False)
    return [result, flags]

def rr_r8(number, flags):
    carry = (flags >> C) & 1
    result = (number >> 1) | (carry << 7)
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, number & 0x01)
  
    return [result, flags]
def rra_r8(number, flags):
    result, flags = rr_r8(number, flags)
    flags = update_bit(flags, Z, False)
    return [result, flags]
def rrc_r8(number, flags):
    result = ((number & 1) << 7) | (number >> 1)
    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, number & 0x01)

    return [result, flags]
def rrca_r8(number, flags):
    result, flags = rrc_r8(number, flags)
    flags = update_bit(flags, Z, False)
    return [result, flags]

def sla_r8(number, flags):
    result = number << 1

    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, number & 0x80)

    return [result, flags] 
def srl_r8(number, flags):
    result = number >> 1

    result = force_d8(result)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, number & 0x01)

    return [result, flags] 
def sra_r8(number, flags):
    result, flags = srl_r8(number, flags)

    # set the bit 7 to it originnal value
    result = (number & 0x80) | (result & 0x7F)
    return [result, flags] 

def swap_r8(number, flags):
    result = (force_d8(number & 0x0F) << 4) | (force_d8(number & 0xF0) >> 4)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, False)
    return [result, flags]

def daa_r8(number, flags):
    
    result = number
    if (flags >> N) & 1:
        if (flags >> C) & 1:
            result -= 0x60
        if (flags >> H) & 1:
            result -= 0x06
    else:
        if ((flags >> C) & 1) or (result > 0x99):
            result += 0x60
            flags = update_bit(flags, C, True)
        if ((flags >> H) & 1) or ((result & 0x0f) > 0x09):
            result += 0x06
            
    
    flags = update_bit(flags, H, False)

    result = force_d8(result)
    flags = update_bit(flags, Z, result == 0)
    return [result, flags]

def cpl_r8(number, flags):
    result = force_d8(~number)
    flags = update_bit(flags, N, True)
    flags = update_bit(flags, H, True)
    return [result, flags]

def scf(number, flags):
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, True)
    return [0, flags]
def ccf(number, flags):
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, False)
    flags = update_bit(flags, C, not ((flags >> C) & 1))
    return [0, flags]

def bit_r8(number, bit, flags):
    # to be tested
    flags = update_bit(flags, Z, not ((number >> bit) & 1))
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, True)
    return [0, flags]
def set_r8(number, bit, flags):
    # to be tested
    result = set_bit(number, bit)
    result = force_d8(result)
    # print("SET {:08b} -> {:08b}".format(number, result))
    return [result, flags]
def res_r8(number, bit, flags):
    result = reset_bit(number, bit)
    result = force_d8(result)
    return [result, flags]   

def dec_r8(number, flags):
    result = force_d8(number - 1)

    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, True)
    flags = update_bit(flags, H, (number & 0x0F) == 0)
    
    return [result, flags]
def inc_r8(number, flags):
    result = force_d8(number + 1)
    
    flags = update_bit(flags, Z, result == 0)
    flags = update_bit(flags, N, False)
    flags = update_bit(flags, H, (number & 0x0F) == 0x0F)

    return [result, flags]
    
# ------------------- alu operations