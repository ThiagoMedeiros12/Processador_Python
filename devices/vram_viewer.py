class VRAMViewer:
    """
    Visualizador ASCII para VRAM no terminal.
    Converte os bytes armazenados na VRAM em uma representação visual formatada.
    """

    RAMPA_PIXELS = " .:-=+*#%@"

    def __init__(self, vram, largura=64, altura=32, modo="auto", char_vazio=" "):
        self.vram = vram
        self.largura = max(1, largura)
        self.altura = max(1, altura)
        self.modo = modo.lower()
        self.char_vazio = char_vazio

    def _obter_bytes(self):
        total = self.largura * self.altura
        dados = []
        limite_vram = len(self.vram.bytes)

        for i in range(total):
            if i < limite_vram:
                dados.append(self.vram.load_byte(i))
            else:
                dados.append(0)

        return dados

    def _resolver_modo(self, dados):
        if self.modo in ("char", "texto", "text"):
            return "char"
        if self.modo in ("pixel", "grafico"):
            return "pixel"

        # Modo "auto": detecta se os bytes não nulos são predominantemente ASCII legíveis
        nao_nulos = [b for b in dados if b != 0]
        if not nao_nulos:
            return "char"

        ascii_imprimivel = sum(1 for b in nao_nulos if 32 <= b <= 126)
        return "char" if (ascii_imprimivel / len(nao_nulos)) >= 0.6 else "pixel"

    def _byte_para_char(self, valor, modo):
        if modo == "char":
            if valor == 0:
                return self.char_vazio
            if 32 <= valor <= 126:
                return chr(valor)
            return "."
        else:
            # Mapeamento para rampa de luminosidade (0..255)
            indice = (valor * (len(self.RAMPA_PIXELS) - 1)) // 255
            return self.RAMPA_PIXELS[indice]

    def renderizar(self, cortar_vazio=True):
        """
        Retorna uma string com o quadro formatado da VRAM.
        Se cortar_vazio for True, remove linhas inferiores totalmente vazias.
        """
        dados = self._obter_bytes()
        modo_efetivo = self._resolver_modo(dados)

        linhas = []
        for y in range(self.altura):
            inicio = y * self.largura
            fim = inicio + self.largura
            linha_chars = "".join(
                self._byte_para_char(b, modo_efetivo) for b in dados[inicio:fim]
            )
            linhas.append(linha_chars)

        if cortar_vazio:
            while len(linhas) > 1 and (
                not linhas[-1] or linhas[-1].strip() == ""
            ):
                linhas.pop()

        borda_horizontal = "+" + "-" * (self.largura + 2) + "+"
        titulo = f" VRAM ({self.largura}x{len(linhas)} - {modo_efetivo.upper()}) "
        if len(titulo) >= len(borda_horizontal) - 2:
            titulo = f" VRAM:{modo_efetivo.upper()} "
            if len(titulo) >= len(borda_horizontal) - 2:
                titulo = ""

        if titulo and len(titulo) < len(borda_horizontal):
            pos = (len(borda_horizontal) - len(titulo)) // 2
            topo = borda_horizontal[:pos] + titulo + borda_horizontal[pos + len(titulo):]
        else:
            topo = borda_horizontal

        resultado = [topo]
        for l in linhas:
            resultado.append(f"| {l} |")
        resultado.append(borda_horizontal)

        return "\n".join(resultado)

    def exibir(self, cortar_vazio=True):
        """Imprime a renderização diretamente no console."""
        quadro = self.renderizar(cortar_vazio=cortar_vazio)
        print(quadro)
        return quadro
