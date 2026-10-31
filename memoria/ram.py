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


class VRAM:
    def __init__(self,tamanho):
        self.bytes = bytearray(tamanho)

    @validar_endereco
    def load_byte(self,endereco):
        return self.bytes[endereco]
    
    @validar_endereco
    def store_byte(self,endereco,valor):
        self.bytes[endereco] = valor & 0xFF
        