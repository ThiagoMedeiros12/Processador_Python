"""
Módulo de Memória Cache (Seção Pontuação Extra 1 do Projeto - 2 pontos)
Implementa uma memória cache com 256 linhas posicionada entre a CPU e o Barramento.
Inclui MMU / Controlador de Cache com gerenciamento de blocos, tags, políticas de
mapeamento (Mapeamento Direto e Associativo em Conjunto com LRU) e estatísticas de Hit/Miss.
"""

from memoria.map_memoria import RAM_INICIO, RAM_FIM


class LinhaCache:
    def __init__(self, tamanho_bloco=16):
        self.valido = False
        self.sujo = False
        self.tag = 0
        self.dados = bytearray(tamanho_bloco)
        self.ultimo_acesso = 0


class CacheMMU:
    """
    Controlador de Memória Cache (MMU) com 256 linhas no total.
    Suporta:
    - 256 linhas configuráveis em:
      * Mapeamento Direto (256 conjuntos x 1 via)
      * Associativo em Conjunto (128 conjuntos x 2 vias ou 64 conjuntos x 4 vias)
    - Política de substituição: LRU (Least Recently Used) ou FIFO
    - Política de escrita: Write-Back com Write-Allocate
    - Bypass automático para regiões de E/S e VRAM (apenas RAM é cacheável)
    """

    def __init__(self, bus, total_linhas=256, vias=1, tamanho_bloco=16, politica_substituicao="LRU"):
        self.bus = bus
        self.total_linhas = total_linhas
        self.vias = max(1, vias)
        self.tamanho_bloco = tamanho_bloco
        self.politica_substituicao = politica_substituicao.upper()

        if total_linhas % self.vias != 0:
            raise ValueError("O número total de linhas deve ser múltiplo do número de vias.")

        self.num_conjuntos = total_linhas // self.vias

        # Matriz de conjuntos: [conjunto_idx][via_idx]
        self.conjuntos = [
            [LinhaCache(tamanho_bloco) for _ in range(self.vias)]
            for _ in range(self.num_conjuntos)
        ]

        # Contadores de estatísticas de desempenho
        self.relogio_acesso = 0
        self.hits_leitura = 0
        self.misses_leitura = 0
        self.hits_escrita = 0
        self.misses_escrita = 0

    def _eh_cacheavel(self, endereco):
        """Apenas a RAM Principal (código, pilha, dados) é cacheada. VRAM e MMIO usam bypass."""
        return RAM_INICIO <= endereco <= RAM_FIM

    def _decompor_endereco(self, endereco):
        """
        Decompõe o endereço em:
        - offset_bloco: bits inferiores correspondentes ao tamanho do bloco
        - indice_conjunto: bits intermediários para selecionar o conjunto
        - tag: bits superiores
        """
        offset_bloco = endereco % self.tamanho_bloco
        bloco_id = endereco // self.tamanho_bloco
        indice_conjunto = bloco_id % self.num_conjuntos
        tag = bloco_id // self.num_conjuntos
        return tag, indice_conjunto, offset_bloco

    def _endereco_base_bloco(self, tag, indice_conjunto):
        """Reconstrói o endereço base (alinhado ao bloco) na memória principal."""
        bloco_id = (tag * self.num_conjuntos) + indice_conjunto
        return bloco_id * self.tamanho_bloco

    def _escrever_bloco_na_memoria(self, linha, tag, indice_conjunto):
        """Write-Back: descarrega linha suja para o barramento."""
        if not (linha.valido and linha.sujo):
            return

        end_base = self._endereco_base_bloco(tag, indice_conjunto)
        for i in range(self.tamanho_bloco):
            self.bus.store_byte(end_base + i, linha.dados[i])
        linha.sujo = False

    def _carregar_bloco_da_memoria(self, linha, tag, indice_conjunto):
        """Carrega bloco da memória para a linha da cache."""
        end_base = self._endereco_base_bloco(tag, indice_conjunto)
        for i in range(self.tamanho_bloco):
            linha.dados[i] = self.bus.load_byte(end_base + i)
        linha.valido = True
        linha.sujo = False
        linha.tag = tag

    def _selecionar_via_substituicao(self, conjunto):
        """Seleciona qual via substituir (uma inválida ou a mais antiga pelo LRU)."""
        for idx, linha in enumerate(conjunto):
            if not linha.valido:
                return idx

        # Política LRU (menor valor de ultimo_acesso)
        menor_acesso = float("inf")
        via_lru = 0
        for idx, linha in enumerate(conjunto):
            if linha.ultimo_acesso < menor_acesso:
                menor_acesso = linha.ultimo_acesso
                via_lru = idx
        return via_lru

    def _acessar_linha(self, endereco, eh_escrita=False):
        """Busca o bloco na cache ou executa preenchimento/substituição."""
        self.relogio_acesso += 1
        tag, indice_conjunto, offset = self._decompor_endereco(endereco)
        conjunto = self.conjuntos[indice_conjunto]

        # Verifica Hit
        for idx, linha in enumerate(conjunto):
            if linha.valido and linha.tag == tag:
                if eh_escrita:
                    self.hits_escrita += 1
                else:
                    self.hits_leitura += 1
                linha.ultimo_acesso = self.relogio_acesso
                return linha, offset

        # Miss de Cache
        if eh_escrita:
            self.misses_escrita += 1
        else:
            self.misses_leitura += 1

        via_idx = self._selecionar_via_substituicao(conjunto)
        linha_alvo = conjunto[via_idx]

        # Se a linha a ser substituída estiver suja, descarrega para a RAM
        if linha_alvo.valido and linha_alvo.sujo:
            self._escrever_bloco_na_memoria(linha_alvo, linha_alvo.tag, indice_conjunto)

        # Carrega o novo bloco
        self._carregar_bloco_da_memoria(linha_alvo, tag, indice_conjunto)
        linha_alvo.ultimo_acesso = self.relogio_acesso
        return linha_alvo, offset

    def load_byte(self, endereco):
        if not self._eh_cacheavel(endereco):
            return self.bus.load_byte(endereco)

        linha, offset = self._acessar_linha(endereco, eh_escrita=False)
        return linha.dados[offset]

    def store_byte(self, endereco, valor):
        if not self._eh_cacheavel(endereco):
            self.bus.store_byte(endereco, valor)
            return

        linha, offset = self._acessar_linha(endereco, eh_escrita=True)
        linha.dados[offset] = valor & 0xFF
        linha.sujo = True

    def load_word(self, endereco):
        if not self._eh_cacheavel(endereco):
            return self.bus.load_word(endereco)

        # Se a palavra cabe no mesmo bloco da cache
        tag, indice_conjunto, offset = self._decompor_endereco(endereco)
        if offset + 4 <= self.tamanho_bloco:
            linha, _ = self._acessar_linha(endereco, eh_escrita=False)
            b0 = linha.dados[offset]
            b1 = linha.dados[offset + 1]
            b2 = linha.dados[offset + 2]
            b3 = linha.dados[offset + 3]
            return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
        else:
            b0 = self.load_byte(endereco)
            b1 = self.load_byte(endereco + 1)
            b2 = self.load_byte(endereco + 2)
            b3 = self.load_byte(endereco + 3)
            return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def store_word(self, endereco, valor):
        if not self._eh_cacheavel(endereco):
            self.bus.store_word(endereco, valor)
            return

        valor &= 0xFFFFFFFF
        tag, indice_conjunto, offset = self._decompor_endereco(endereco)
        if offset + 4 <= self.tamanho_bloco:
            linha, _ = self._acessar_linha(endereco, eh_escrita=True)
            linha.dados[offset] = valor & 0xFF
            linha.dados[offset + 1] = (valor >> 8) & 0xFF
            linha.dados[offset + 2] = (valor >> 16) & 0xFF
            linha.dados[offset + 3] = (valor >> 24) & 0xFF
            linha.sujo = True
        else:
            self.store_byte(endereco, valor & 0xFF)
            self.store_byte(endereco + 1, (valor >> 8) & 0xFF)
            self.store_byte(endereco + 2, (valor >> 16) & 0xFF)
            self.store_byte(endereco + 3, (valor >> 24) & 0xFF)

    def flush(self):
        """Descarrega todas as linhas sujas para a memória principal."""
        for indice_conjunto, conjunto in enumerate(self.conjuntos):
            for linha in conjunto:
                if linha.valido and linha.sujo:
                    self._escrever_bloco_na_memoria(linha, linha.tag, indice_conjunto)

    def relatorio_estatisticas(self):
        """Retorna resumo detalhado de desempenho da cache."""
        total_leituras = self.hits_leitura + self.misses_leitura
        total_escritas = self.hits_escrita + self.misses_escrita
        total_acessos = total_leituras + total_escritas
        total_hits = self.hits_leitura + self.hits_escrita
        total_misses = self.misses_leitura + self.misses_escrita

        taxa_hit = (total_hits / total_acessos * 100) if total_acessos > 0 else 0.0
        taxa_miss = (total_misses / total_acessos * 100) if total_acessos > 0 else 0.0

        tipo_map = "Mapeamento Direto" if self.vias == 1 else f"Associativo em Conjunto ({self.vias} vias, LRU)"

        linhas = [
            "=" * 64,
            f"  ESTATÍSTICAS DA MEMÓRIA CACHE ({self.total_linhas} LINHAS - {tipo_map})",
            "=" * 64,
            f"  Total de Acessos:     {total_acessos:<8} (Leituras: {total_leituras}, Escritas: {total_escritas})",
            f"  Cache Hits:           {total_hits:<8} (Leituras: {self.hits_leitura}, Escritas: {self.hits_escrita})",
            f"  Cache Misses:         {total_misses:<8} (Leituras: {self.misses_leitura}, Escritas: {self.misses_escrita})",
            f"  Taxa de Acerto (Hit): {taxa_hit:.2f}%",
            f"  Taxa de Falha (Miss): {taxa_miss:.2f}%",
            "=" * 64,
        ]
        return "\n".join(linhas)

    # Encaminha chamadas de controle de interrupção para o barramento
    def solicitar_interrupcao(self, codigo=1):
        return self.bus.solicitar_interrupcao(codigo)

    def verificar_interrupcao(self):
        return self.bus.verificar_interrupcao()

    def atender_interrupcao(self):
        return self.bus.atender_interrupcao()

    @property
    def ram(self):
        return self.bus.ram

    @property
    def vram(self):
        return self.bus.vram

    @property
    def io_device(self):
        return self.bus.io_device
