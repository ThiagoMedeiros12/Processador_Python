import pytest
from memoria.bus import Bus
from memoria.cache import CacheMMU
from memoria.map_memoria import RAM_INICIO, VRAM_INICIO, IO_INICIO


@pytest.fixture
def bus():
    return Bus()


@pytest.fixture
def cache(bus):
    # Cache padrão de 256 linhas com mapeamento direto
    return CacheMMU(bus, total_linhas=256, vias=1, tamanho_bloco=16)


def test_cache_miss_seguido_de_hit(cache):
    # Primeiro acesso à palavra em 0x100: deve gerar Miss de leitura
    cache.store_word(0x100, 0x12345678)
    # Acessos seguintes ao mesmo bloco (offset 0 e offset 4) devem ser Hits
    val0 = cache.load_word(0x100)
    assert val0 == 0x12345678
    assert cache.hits_leitura >= 1


def test_cache_localidade_espacial(cache):
    # Bloco de 16 bytes: 0x200 a 0x20F
    cache.bus.store_word(0x200, 0x11111111)
    cache.bus.store_word(0x204, 0x22222222)
    cache.bus.store_word(0x208, 0x33333333)
    cache.bus.store_word(0x20C, 0x44444444)

    # Primeira leitura: Miss (traz o bloco inteiro de 16 bytes)
    assert cache.load_word(0x200) == 0x11111111
    assert cache.misses_leitura == 1
    assert cache.hits_leitura == 0

    # Próximas leituras no mesmo bloco: Hits!
    assert cache.load_word(0x204) == 0x22222222
    assert cache.load_word(0x208) == 0x33333333
    assert cache.load_word(0x20C) == 0x44444444
    assert cache.misses_leitura == 1
    assert cache.hits_leitura == 3


def test_cache_write_back_e_flush(bus, cache):
    endereco = 0x300
    cache.store_word(endereco, 0xAABBCCDD)

    # Antes do flush, o dado está na cache (linha suja), mas não necessariamente na RAM
    # Executa o flush: descarrega blocos sujos na RAM
    cache.flush()
    assert bus.ram.load_word(endereco) == 0xAABBCCDD


def test_cache_associativa_lru(bus):
    # 256 linhas configuradas em 2 vias (128 conjuntos)
    cache_2way = CacheMMU(bus, total_linhas=256, vias=2, tamanho_bloco=16, politica_substituicao="LRU")

    # Dois endereços com o mesmo índice de conjunto mas tags diferentes
    # tamanho_bloco = 16, num_conjuntos = 128 -> periodo = 16 * 128 = 2048 (0x800)
    end1 = 0x100
    end2 = 0x100 + 0x800  # Mesmo conjunto
    end3 = 0x100 + 0x1000 # Terceiro bloco para o mesmo conjunto (força substituição LRU)

    cache_2way.store_word(end1, 100)
    cache_2way.store_word(end2, 200)

    # Ambos devem estar na cache (pois temos 2 vias!)
    assert cache_2way.load_word(end1) == 100
    assert cache_2way.load_word(end2) == 200

    # Acessa end1 para torná-lo mais recente que end2
    _ = cache_2way.load_word(end1)

    # Agora insere end3: deve substituir end2 (o menos recentemente usado - LRU)
    cache_2way.store_word(end3, 300)

    assert cache_2way.load_word(end1) == 100  # Permaneceu na cache
    assert cache_2way.load_word(end3) == 300  # Novo bloco


def test_cache_bypass_vram_e_io(cache):
    # VRAM e MMIO não devem ser cacheados
    cache.store_byte(VRAM_INICIO + 0x10, 0xAB)
    assert cache.bus.vram.load_byte(0x10) == 0xAB

    # Registradores MMIO
    cache.store_byte(IO_INICIO + 4, ord("X"))
    assert cache.bus.io_device.read_output() == b"X"


def test_cache_estatisticas_formatacao(cache):
    cache.store_word(0x400, 42)
    _ = cache.load_word(0x400)
    relatorio = cache.relatorio_estatisticas()

    assert "ESTATÍSTICAS DA MEMÓRIA CACHE (256 LINHAS" in relatorio
    assert "Taxa de Acerto (Hit):" in relatorio
    assert "Taxa de Falha (Miss):" in relatorio
