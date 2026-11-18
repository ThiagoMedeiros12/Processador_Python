import pytest
from memoria.bus import Bus
from memoria.map_memoria import RAM_FIM
from programs.loader import carregar_programa


@pytest.fixture
def bus():
    return Bus()


def test_carregar_programa_valido(bus, tmp_path):
    arquivo = tmp_path / "programa.hex"
    arquivo.write_text(
        """
        # Teste de comentário
        00500113 // addi x2, x0, 5
        00300193 ; addi x3, x0, 3

        00310233 # add x4, x2, x3
        00100073 // ebreak
        """,
        encoding="utf-8"
    )

    retorno = carregar_programa(str(arquivo), bus, endereco_inicial=0)
    assert retorno == 0

    assert bus.load_word(0x00) == 0x00500113
    assert bus.load_word(0x04) == 0x00300193
    assert bus.load_word(0x08) == 0x00310233
    assert bus.load_word(0x0C) == 0x00100073


def test_carregar_programa_arquivo_inexistente(bus):
    with pytest.raises(FileNotFoundError):
        carregar_programa("arquivo_que_nao_existe.hex", bus)


def test_carregar_programa_hex_invalido(bus, tmp_path):
    arquivo = tmp_path / "invalido.hex"
    arquivo.write_text("00500113\nNAO_EH_HEX\n00100073\n", encoding="utf-8")

    with pytest.raises(ValueError, match="não é um hexadecimal válido"):
        carregar_programa(str(arquivo), bus)


def test_carregar_programa_valor_maior_32_bits(bus, tmp_path):
    arquivo = tmp_path / "overflow.hex"
    arquivo.write_text("100000000\n", encoding="utf-8")  # 33 bits

    with pytest.raises(ValueError, match="fora do limite de 32 bits"):
        carregar_programa(str(arquivo), bus)


def test_carregar_programa_desalinhado(bus, tmp_path):
    arquivo = tmp_path / "prog.hex"
    arquivo.write_text("00100073\n", encoding="utf-8")

    with pytest.raises(ValueError, match="alinhado"):
        carregar_programa(str(arquivo), bus, endereco_inicial=1)


def test_carregar_programa_excede_ram(bus, tmp_path):
    arquivo = tmp_path / "grande.hex"
    arquivo.write_text("00100073\n00100073\n", encoding="utf-8")

    # Começa perto do final da RAM onde a segunda instrução estoura
    endereco_quase_fim = RAM_FIM - 3
    with pytest.raises(ValueError, match="excede o limite da RAM"):
        carregar_programa(str(arquivo), bus, endereco_inicial=endereco_quase_fim)
