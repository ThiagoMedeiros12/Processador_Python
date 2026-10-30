
class RAM:
    def __init__(self, tamanho):
        self.bytes = bytearray(tamanho)

    def _validar(self, endereco):
        if endereco < 0 or endereco >= len(self.bytes):
            raise ValueError("Endereço fora da RAM")

    def load_byte(self, endereco):
        self._validar(endereco)
        return self.bytes[endereco]

    def store_byte(self, endereco, valor):
        self._validar(endereco)
        self.bytes[endereco] = valor & 0xFF

    def load_word(self, endereco):
        if endereco % 4 != 0:
            raise ValueError("Endereço de palavra não alinhado")

        b0 = self.load_byte(endereco)
        b1 = self.load_byte(endereco + 1)
        b2 = self.load_byte(endereco + 2)
        b3 = self.load_byte(endereco + 3)

        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def store_word(self, endereco, valor):
        if endereco % 4 != 0:
            raise ValueError("Endereço de palavra não alinhado")

        valor &= 0xFFFFFFFF

        self.store_byte(endereco, valor & 0xFF)
        self.store_byte(endereco + 1, (valor >> 8) & 0xFF)
        self.store_byte(endereco + 2, (valor >> 16) & 0xFF)
        self.store_byte(endereco + 3, (valor >> 24) & 0xFF)
