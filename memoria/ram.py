from functools import wraps

def validar_endereco(func):
    @wraps(func)
    def wrapper(self, endereco, *args, **kwargs):

        if isinstance(endereco, bool) or not isinstance(endereco, int):
            raise TypeError("Endereço precisa ser inteiro")

        if endereco < 0 or endereco >= len(self.bytes):
            raise ValueError(f"Endereco fora da {self.__class__.__name__}")
        return func(self, endereco, *args, **kwargs)    
    return wrapper

def validar_word(func):
    @wraps(func)
    def wrapper(self, endereco, *args, **kwargs):

        if isinstance(endereco, bool) or not isinstance(endereco, int):
            raise TypeError("Endereco precisa ser inteiro")

        if endereco % 4 != 0:
            raise ValueError("Endereco de palavra nao alinhado")

        if endereco < 0 or endereco + 4 > len(self.bytes):
            raise ValueError("Endereco fora da RAM")

        return func(self, endereco, *args, **kwargs)   
    return wrapper


class RAM:
    def __init__(self, tamanho):
        self.bytes = bytearray(tamanho)

    @validar_endereco
    def load_byte(self, endereco):
        return self.bytes[endereco]

    @validar_endereco
    def store_byte(self, endereco, valor):
        self.bytes[endereco] = valor & 0xFF

    @validar_word
    def load_word(self, endereco):

        b0 = self.load_byte(endereco)
        b1 = self.load_byte(endereco + 1)
        b2 = self.load_byte(endereco + 2)
        b3 = self.load_byte(endereco + 3)

        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    @validar_word
    def store_word(self, endereco, valor):

        valor &= 0xFFFFFFFF
        self.store_byte(endereco, valor & 0xFF)
        self.store_byte(endereco + 1, (valor >> 8) & 0xFF)
        self.store_byte(endereco + 2, (valor >> 16) & 0xFF)
        self.store_byte(endereco + 3, (valor >> 24) & 0xFF)

    def dump_matriz_32_colunas(self, endereco_inicial=0, num_linhas=8, omitir_vazias=False):
        """
        Retorna a memória formatada como uma matriz de exatamente 32 colunas (32 bytes por linha),
        conforme especificado na Seção 3 do projeto.
        """
        if endereco_inicial < 0 or endereco_inicial >= len(self.bytes):
            raise ValueError("Endereço inicial fora dos limites da RAM")

        colunas = 32
        linhas_resultado = []

        # Cabeçalho com as 32 colunas numeradas de 0x00 a 0x1F
        cabecalho_hex = " ".join(f"{c:02X}" for c in range(colunas))
        divisor = "=" * 115
        linhas_resultado.append(divisor)
        linhas_resultado.append(f"  MATRIZ DE MEMÓRIA RAM (32 COLUNAS) - Início: 0x{endereco_inicial:05X}")
        linhas_resultado.append(divisor)
        linhas_resultado.append(f"Endereço | {cabecalho_hex} | ASCII (32 colunas)")
        linhas_resultado.append("-" * 115)

        total_bytes = len(self.bytes)
        for i in range(num_linhas):
            offset = endereco_inicial + (i * colunas)
            if offset >= total_bytes:
                break

            fim = min(offset + colunas, total_bytes)
            fatia = self.bytes[offset:fim]

            if omitir_vazias and all(b == 0 for b in fatia):
                continue

            hex_bytes = " ".join(f"{b:02X}" for b in fatia)
            # Preenche se a última linha tiver menos de 32 bytes
            if len(fatia) < colunas:
                hex_bytes = hex_bytes.ljust(colunas * 3 - 1)

            ascii_repr = "".join(chr(b) if 32 <= b <= 126 else "." for b in fatia)

            linhas_resultado.append(f"0x{offset:05X}  | {hex_bytes} | {ascii_repr}")

        linhas_resultado.append(divisor)
        return "\n".join(linhas_resultado)


