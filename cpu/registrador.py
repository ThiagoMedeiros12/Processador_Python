
MASK32 = 0xFFFFFFFF

def validar_registrador(func):
    
    def wrapper(self, index, *args, **kwargs):
        if not isinstance(index, int) or isinstance(index,bool):
            raise TypeError("O índice deve ser um inteiro")
        if not 0 <= index <31: 
            raise ValueError("Registrador fora do intervalo")
        return func(self, index,*args, **kwargs)
    return wrapper


class RegisterFile:
    def __init__(self):
        self.values = [0] * 32

    @validar_registrador
    def read(self, index):
        if index == 0:
            return 0
        return self.values[index] & MASK32

    @validar_registrador
    def write(self, index, value):
        if index == 0:
            return
        self.values[index] = value & MASK32