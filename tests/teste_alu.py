import pytest
from cpu.alu import ALU, clz32


@pytest.mark.parametrize("entrada, esperado", [
    (0x00000000, 32),
    (0x00000001, 31),
    (0x00000002, 30),
    (0x00000008, 28),
    (0x80000000, 0),
    (0xFFFFFFFF, 0),
])
def test_clz32(entrada, esperado):
    assert clz32(entrada) == esperado
    assert ALU.clz(entrada) == esperado


def test_alu_add():
    assert ALU.add(10, 20) == 30
    assert ALU.add(0xFFFFFFFF, 1) == 0  # Overflow wrapping 32-bit
    assert ALU.add(0xFFFFFFFF, 0xFFFFFFFF) == 0xFFFFFFFE


def test_alu_sub():
    assert ALU.sub(50, 20) == 30
    assert ALU.sub(0, 1) == 0xFFFFFFFF  # Underflow wrapping 32-bit
    assert ALU.sub(10, 10) == 0


def test_alu_sll():
    assert ALU.sll(1, 4) == 16
    assert ALU.sll(0x80000000, 1) == 0
    # Apenas os 5 bits inferiores do shamt são considerados (36 % 32 = 4)
    assert ALU.sll(1, 36) == 16


def test_alu_srl():
    assert ALU.srl(16, 4) == 1
    assert ALU.srl(0x80000000, 1) == 0x40000000
    assert ALU.srl(16, 36) == 1


def test_alu_sra():
    # Deslocamento aritmético preserva o sinal (MSB)
    assert ALU.sra(16, 2) == 4
    assert ALU.sra(0x80000000, 1) == 0xC0000000
    assert ALU.sra(0xFFFFFFFF, 4) == 0xFFFFFFFF


def test_alu_slt_sltu():
    # SLT: com sinal (-1 < 1 é True)
    assert ALU.slt(0xFFFFFFFF, 1) == 1
    assert ALU.slt(1, 0xFFFFFFFF) == 0
    assert ALU.slt(5, 5) == 0

    # SLTU: sem sinal (0xFFFFFFFF > 1)
    assert ALU.sltu(0xFFFFFFFF, 1) == 0
    assert ALU.sltu(1, 0xFFFFFFFF) == 1
    assert ALU.sltu(5, 5) == 0


def test_alu_bitwise():
    assert ALU.xor(0b1100, 0b1010) == 0b0110
    assert ALU.or_(0b1100, 0b1010) == 0b1110
    assert ALU.and_(0b1100, 0b1010) == 0b1000


def test_alu_executar_despacho():
    assert ALU.executar("ADD", 10, 5) == 15
    assert ALU.executar("ADDI", 10, -5) == 5
    assert ALU.executar("SUB", 10, 5) == 5
    assert ALU.executar("SLL", 2, 3) == 16
    assert ALU.executar("SLLI", 2, 3) == 16
    assert ALU.executar("SLT", -10, 5) == 1
    assert ALU.executar("SLTI", -10, 5) == 1
    assert ALU.executar("SLTU", -10, 5) == 0
    assert ALU.executar("SLTIU", -10, 5) == 0
    assert ALU.executar("XOR", 15, 10) == 5
    assert ALU.executar("XORI", 15, 10) == 5
    assert ALU.executar("SRL", 32, 2) == 8
    assert ALU.executar("SRLI", 32, 2) == 8
    assert ALU.executar("SRA", 0x80000000, 1) == 0xC0000000
    assert ALU.executar("SRAI", 0x80000000, 1) == 0xC0000000
    assert ALU.executar("OR", 4, 2) == 6
    assert ALU.executar("ORI", 4, 2) == 6
    assert ALU.executar("AND", 6, 2) == 2
    assert ALU.executar("ANDI", 6, 2) == 2
    assert ALU.executar("CLZ", 0x00000001) == 31

    with pytest.raises(ValueError, match="Operacao ALU desconhecida"):
        ALU.executar("UNKNOWN", 1, 2)
