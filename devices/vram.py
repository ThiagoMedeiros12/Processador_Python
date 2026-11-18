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

class VRAM:
    def __init__(self,tamanho):
        self.bytes = bytearray(tamanho)

    @validar_endereco
    def load_byte(self,endereco):
        return self.bytes[endereco]
    
    @validar_endereco
    def store_byte(self,endereco,valor):
        self.bytes[endereco] = valor & 0xFF