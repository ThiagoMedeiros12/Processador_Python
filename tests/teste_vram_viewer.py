import pytest
from devices.vram import VRAM
from devices.vram_viewer import VRAMViewer


@pytest.fixture
def vram():
    return VRAM(0x10000)


def test_vram_viewer_modo_char(vram):
    texto = "TESTE_ASCII"
    for i, ch in enumerate(texto):
        vram.store_byte(i, ord(ch))

    viewer = VRAMViewer(vram, largura=16, altura=4, modo="char")
    saida = viewer.renderizar(cortar_vazio=True)

    assert "TESTE_ASCII" in saida
    assert saida.startswith("+")
    assert saida.endswith("+")


def test_vram_viewer_modo_pixel(vram):
    # Valores com diferentes intensidades
    valores = [0, 64, 128, 192, 255]
    for i, v in enumerate(valores):
        vram.store_byte(i, v)

    viewer = VRAMViewer(vram, largura=5, altura=1, modo="pixel")
    saida = viewer.renderizar(cortar_vazio=False)

    # 0 deve ser ' ' e 255 deve ser '@'
    assert " " in saida
    assert "@" in saida


def test_vram_viewer_modo_auto(vram):
    banner = "HELLO WORLD"
    for i, ch in enumerate(banner):
        vram.store_byte(i, ord(ch))

    viewer = VRAMViewer(vram, largura=16, altura=2, modo="auto")
    saida = viewer.renderizar(cortar_vazio=True)

    assert "HELLO WORLD" in saida
    assert "CHAR" in saida  # Título deve indicar detecção do modo CHAR


def test_vram_viewer_vazio(vram):
    viewer = VRAMViewer(vram, largura=10, altura=4, modo="auto")
    saida = viewer.renderizar(cortar_vazio=True)

    # Deve renderizar pelo menos 1 linha
    assert "+------------+" in saida
