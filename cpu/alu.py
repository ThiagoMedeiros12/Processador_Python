MASK32 = 0xFFFFFFFF

def clz32(value):
    value = value & MASK32
    
    if value == 0:
        return 32
    return 32 - value.bit_length()