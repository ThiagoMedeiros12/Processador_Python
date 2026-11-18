import pytest
from cpu.registrador import RegisterFile


@pytest.fixture
def regs():
    return RegisterFile()


def test_escrita_e_leitura(regs):
    regs.write(1, 123)
    assert regs.read(1) == 123


def test_registrador_x0_sempre_zero(regs):
    regs.write(0, 999)
    assert regs.read(0) == 0