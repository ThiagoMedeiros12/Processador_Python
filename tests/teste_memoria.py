import pytest
from memoria.ram import RAM
from devices.vram import VRAM
from memoria.bus import (
    Bus,
    RAM_INICIO,
    RAM_FIM,
    VRAM_INICIO,
    VRAM_FIM,
    RESERVADO_INICIO,
    IO_INICIO,
    IO_FIM,
)


@pytest.fixture
def ram():
    return RAM(1024)


@pytest.fixture
def vram():
    return VRAM(0x10000)


@pytest.fixture
def bus():
    return Bus()


# ==================== TESTES DA RAM ====================

def test_ram_byte(ram):
    ram.store_byte(0x00, 0x4F)
    ram.store_byte(0x01, 0x49)
    assert ram.load_byte(0x00) == 0x4F
    assert ram.load_byte(0x01) == 0x49


def test_ram_word_little_endian(ram):
    ram.store_word(0x04, 0x12345678)
    assert ram.load_byte(0x04) == 0x78
    assert ram.load_byte(0x05) == 0x56
    assert ram.load_byte(0x06) == 0x34
    assert ram.load_byte(0x07) == 0x12
    assert ram.load_word(0x04) == 0x12345678


def test_ram_word_limite(ram):
    ram.store_word(1020, 0xAABBCCDD)
    assert ram.load_word(1020) == 0xAABBCCDD


def test_ram_excecoes(ram):
    with pytest.raises(ValueError, match="(?i)alinhado"):
        ram.load_word(0x05)

    with pytest.raises(ValueError, match="(?i)ram"):
        ram.load_byte(1024)

    with pytest.raises(ValueError):
        ram.load_byte(-1)

    with pytest.raises(TypeError):
        ram.load_byte("10")

    with pytest.raises(ValueError):
        ram.store_word(1024, 0x12345678)


# ==================== TESTES DA VRAM ====================

def test_vram_tamanho_e_bytes(vram):
    assert len(vram.bytes) == 0x10000

    vram.store_byte(0x00, 0x4F)
    vram.store_byte(0x01, 0x49)
    assert vram.load_byte(0x00) == 0x4F
    assert vram.load_byte(0x01) == 0x49

    vram.store_byte(0x1000, 0xAB)
    assert vram.load_byte(0x1000) == 0xAB

    vram.store_byte(0xFFFF, 0xFF)
    assert vram.load_byte(0xFFFF) == 0xFF


def test_vram_mascara_byte(vram):
    vram.store_byte(0x10, 0x1234)
    assert vram.load_byte(0x10) == 0x34


def test_vram_excecoes(vram):
    with pytest.raises(ValueError, match="(?i)vram"):
        vram.load_byte(0x10000)

    with pytest.raises(ValueError):
        vram.load_byte(-1)

    with pytest.raises(TypeError):
        vram.load_byte("10")


# ==================== TESTES DO BUS ====================

def test_bus_ram_byte_e_word(bus):
    bus.store_byte(RAM_INICIO, 0x4F)
    assert bus.load_byte(RAM_INICIO) == 0x4F

    endereco = RAM_INICIO + 4
    bus.store_word(endereco, 0x12345678)
    assert bus.load_word(endereco) == 0x12345678
    assert bus.load_byte(endereco) == 0x78
    assert bus.load_byte(endereco + 1) == 0x56
    assert bus.load_byte(endereco + 2) == 0x34
    assert bus.load_byte(endereco + 3) == 0x12


def test_bus_vram_byte_e_word(bus):
    bus.store_byte(VRAM_INICIO, 0xAB)
    assert bus.load_byte(VRAM_INICIO) == 0xAB

    endereco_vram = VRAM_INICIO + 4
    bus.store_word(endereco_vram, 0xAABBCCDD)
    assert bus.load_word(endereco_vram) == 0xAABBCCDD


def test_bus_limites_validos(bus):
    bus.store_word(RAM_FIM - 3, 0xAABBCCDD)
    assert bus.load_word(RAM_FIM - 3) == 0xAABBCCDD

    bus.store_word(VRAM_FIM - 3, 0x11223344)
    assert bus.load_word(VRAM_FIM - 3) == 0x11223344


@pytest.mark.parametrize("endereco_invalido", [
    -1,
    IO_FIM + 1,
    0xA0000,
])
def test_bus_enderecos_fora_do_mapa(bus, endereco_invalido):
    with pytest.raises(ValueError):
        bus.load_byte(endereco_invalido)


def test_bus_regiao_reservada_e_io(bus):
    with pytest.raises(ValueError, match="(?i)reservada"):
        bus.load_byte(RESERVADO_INICIO)

    with pytest.raises(ValueError, match="(?i)reservada"):
        bus.store_byte(0x90000, 99)

    # Testa a leitura do registrador DATA_IN
    bus.io_device.queue_input(ord("A"))

    assert bus.load_byte(IO_INICIO) == ord("A")

    # Testa a escrita no registrador DATA_OUT
    bus.store_byte(IO_INICIO + 4, ord("B"))

    assert bus.io_device.read_output() == b"B"

    # Após ler DATA_IN, STATUS deve indicar que não há entrada disponível
    assert bus.load_byte(IO_INICIO + 8) == 0


def test_bus_alinhamento_e_fronteira(bus):
    with pytest.raises(ValueError, match="(?i)alinhado"):
        bus.load_word(RAM_INICIO + 1)

    with pytest.raises(ValueError, match="(?i)alinhado"):
        bus.load_word(0x00002)

    with pytest.raises(ValueError):
        bus.load_word(RAM_FIM + 1 - 3)


def test_bus_validacao_tipos_e_valores(bus):
    with pytest.raises(TypeError):
        bus.load_byte("100")

    with pytest.raises(ValueError):
        bus.store_byte(RAM_INICIO + 0x10, 256)

    with pytest.raises(TypeError):
        bus.store_byte(RAM_INICIO + 0x10, True)