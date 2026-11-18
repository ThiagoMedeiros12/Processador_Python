
class Terminal:

    def __init__(self, io_device, encoding="utf-8"):
        self.io_device = io_device
        self.encoding = encoding
        self.posicao_saida = 0

    def enviar_entrada(self, texto):
        """
        Envia texto para o dispositivo de I/O.
        Cada caractere é convertido em bytes UTF-8.
        """

        if not isinstance(texto, str):
            raise TypeError("A entrada precisa ser uma string")

        dados = texto.encode(self.encoding)

        for byte in dados:
            self.io_device.queue_input(byte)

    def solicitar_entrada(self):
        """
        Solicita texto ao usuário pelo console.
        """

        texto = input("Entrada: ")
        self.enviar_entrada(texto)

    def obter_saida(self):
        """
        Recupera somente os bytes de saída ainda não apresentados.
        """

        dados = self.io_device.read_output()

        novos_dados = dados[self.posicao_saida:]

        self.posicao_saida = len(dados)

        return novos_dados.decode(self.encoding)

    def exibir_saida(self):
        """
        Apresenta a saída produzida pela CPU.
        """

        texto = self.obter_saida()

        print(texto, end="", flush=True)

        return texto
