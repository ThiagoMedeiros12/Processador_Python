
import pytest

from devices.io import IODevice
from devices.terminal import Terminal


@pytest.fixture
def ambiente_terminal():
    io_device = IODevice()
    terminal = Terminal(io_device)

    return terminal, io_device


def test_terminal_enviar_entrada(ambiente_terminal):
    terminal, io_device = ambiente_terminal

    terminal.enviar_entrada("ABC")

    assert io_device.load_byte(0x000) == ord("A")
    assert io_device.load_byte(0x000) == ord("B")
    assert io_device.load_byte(0x000) == ord("C")


def test_terminal_status_entrada(ambiente_terminal):
    terminal, io_device = ambiente_terminal

    assert io_device.load_byte(0x008) == 0

    terminal.enviar_entrada("A")

    assert io_device.load_byte(0x008) == 1

    assert io_device.load_byte(0x000) == ord("A")

    assert io_device.load_byte(0x008) == 0


def test_terminal_receber_saida(ambiente_terminal):
    terminal, io_device = ambiente_terminal

    io_device.store_byte(0x004, ord("O"))
    io_device.store_byte(0x004, ord("I"))

    assert terminal.obter_saida() == "OI"


def test_terminal_nao_repetir_saida(ambiente_terminal):
    terminal, io_device = ambiente_terminal

    io_device.store_byte(0x004, ord("A"))

    assert terminal.obter_saida() == "A"
    assert terminal.obter_saida() == ""


def test_terminal_texto_utf8(ambiente_terminal):
    terminal, io_device = ambiente_terminal

    terminal.enviar_entrada("Olá")

    dados = [
        io_device.load_byte(0x000),
        io_device.load_byte(0x000),
        io_device.load_byte(0x000),
        io_device.load_byte(0x000),
    ]

    assert bytes(dados).decode("utf-8") == "Olá"


def test_terminal_entrada_invalida(ambiente_terminal):
    terminal, _ = ambiente_terminal

    with pytest.raises(TypeError):
        terminal.enviar_entrada(123)


def test_io_device_dispara_interrupcao_ao_receber_tecla():
    from memoria.bus import Bus
    bus = Bus()
    terminal = Terminal(bus.io_device)

    assert bus.verificar_interrupcao() is False
    terminal.enviar_entrada("K")
    assert bus.verificar_interrupcao() is True

    # Atende a interrupção e verifica que o dado está no registrador DATA_IN
    bus.atender_interrupcao()
    assert bus.load_byte(0x9FC00) == ord("K")

