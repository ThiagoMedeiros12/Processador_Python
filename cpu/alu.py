MASK32 = 0xFFFFFFFF


def estender_sinal(valor, bits):
    sinal = 1 << (bits - 1)
    return (valor & (sinal - 1)) - (valor & sinal)


def clz32(value):
    value = value & MASK32
    if value == 0:
        return 32
    return 32 - value.bit_length()


class ALU:
    """Unidade Lógica e Aritmética (ALU) para processador RISC-V RV32I + Zbb (CLZ)."""

    @staticmethod
    def add(a, b):
        return (a + b) & MASK32

    @staticmethod
    def sub(a, b):
        return (a - b) & MASK32

    @staticmethod
    def sll(a, b):
        return ((a & MASK32) << (b & 0x1F)) & MASK32

    @staticmethod
    def slt(a, b):
        sa = estender_sinal(a & MASK32, 32)
        sb = estender_sinal(b & MASK32, 32)
        return 1 if sa < sb else 0

    @staticmethod
    def sltu(a, b):
        ua = a & MASK32
        ub = b & MASK32
        return 1 if ua < ub else 0

    @staticmethod
    def xor(a, b):
        return ((a & MASK32) ^ (b & MASK32)) & MASK32

    @staticmethod
    def srl(a, b):
        return ((a & MASK32) >> (b & 0x1F)) & MASK32

    @staticmethod
    def sra(a, b):
        sa = estender_sinal(a & MASK32, 32)
        return (sa >> (b & 0x1F)) & MASK32

    @staticmethod
    def or_(a, b):
        return ((a & MASK32) | (b & MASK32)) & MASK32

    @staticmethod
    def and_(a, b):
        return ((a & MASK32) & (b & MASK32)) & MASK32

    @staticmethod
    def clz(a):
        return clz32(a)

    @classmethod
    def executar(cls, operacao, op1, op2=0):
        op = operacao.upper()

        if op in ("ADD", "ADDI"):
            return cls.add(op1, op2)
        elif op == "SUB":
            return cls.sub(op1, op2)
        elif op in ("SLL", "SLLI"):
            return cls.sll(op1, op2)
        elif op in ("SLT", "SLTI"):
            return cls.slt(op1, op2)
        elif op in ("SLTU", "SLTIU"):
            return cls.sltu(op1, op2)
        elif op in ("XOR", "XORI"):
            return cls.xor(op1, op2)
        elif op in ("SRL", "SRLI"):
            return cls.srl(op1, op2)
        elif op in ("SRA", "SRAI"):
            return cls.sra(op1, op2)
        elif op in ("OR", "ORI"):
            return cls.or_(op1, op2)
        elif op in ("AND", "ANDI"):
            return cls.and_(op1, op2)
        elif op == "CLZ":
            return cls.clz(op1)
        else:
            raise ValueError(f"Operacao ALU desconhecida: {operacao}")
