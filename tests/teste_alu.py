import pytest
from cpu.alu import clz32


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