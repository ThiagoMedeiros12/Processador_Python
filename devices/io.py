
from collections import deque


class IODevice:

    DATA_IN = 0x000
    DATA_OUT = 0x004
    STATUS = 0x008

    def __init__(self):
        self.input_queue = deque()
        self.data_out = 0
        self.output_log = []

    @property
    def input_ready(self):
        return len(self.input_queue) > 0

    def load_byte(self, offset):

        if offset == self.DATA_IN:

            if not self.input_queue:
                return 0

            return self.input_queue.popleft()

        if offset == self.DATA_OUT:
            return self.data_out

        if offset == self.STATUS:
            return 1 if self.input_ready else 0

        raise ValueError("Registrador I/O invalido")

    def store_byte(self, offset, value):

        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("Valor precisa ser inteiro")

        if not 0 <= value <= 0xFF:
            raise ValueError("Valor deve caber em 8 bits")

        if offset in (self.DATA_IN, self.STATUS):
            raise ValueError("Registrador somente leitura")

        if offset == self.DATA_OUT:
            self.data_out = value
            self.output_log.append(value)
            return

        raise ValueError("Registrador I/O invalido")

    def queue_input(self, value):

        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("Entrada precisa ser inteira")

        if not 0 <= value <= 0xFF:
            raise ValueError("Entrada deve caber em 8 bits")

        self.input_queue.append(value)

    def read_output(self):
        return bytes(self.output_log)
