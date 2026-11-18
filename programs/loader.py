import os
from memoria.map_memoria import RAM_INICIO, RAM_FIM


def carregar_programa(caminho, bus, endereco_inicial=0):
    """
    Carrega instruções em formato hexadecimal de um arquivo para a memória RAM via Bus.

    Suporta:
    - Linhas com comentários iniciados por '#', '//' ou ';'
    - Linhas em branco e espaços adicionais
    - Valores hexadecimais de 32 bits (com ou sem prefixo '0x')

    Lança:
    - FileNotFoundError: caso o arquivo não exista.
    - ValueError: caso haja valor inválido ou o código ultrapasse a RAM.
    """
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if endereco_inicial % 4 != 0:
        raise ValueError(f"Endereço inicial deve ser alinhado a 4 bytes: 0x{endereco_inicial:X}")

    endereco = endereco_inicial

    with open(caminho, "r", encoding="utf-8") as arquivo:
        for num_linha, linha in enumerate(arquivo, start=1):
            # Remover comentários
            for delimitador in ("#", "//", ";"):
                linha = linha.split(delimitador)[0]

            linha = linha.strip()
            if not linha:
                continue

            try:
                instrucao = int(linha, 16)
            except ValueError:
                raise ValueError(
                    f"Erro na linha {num_linha} de '{caminho}': '{linha}' não é um hexadecimal válido"
                )

            if not 0 <= instrucao <= 0xFFFFFFFF:
                raise ValueError(
                    f"Instrução fora do limite de 32 bits na linha {num_linha}: 0x{instrucao:X}"
                )

            if endereco < RAM_INICIO or (endereco + 3) > RAM_FIM:
                raise ValueError(
                    f"Programa excede o limite da RAM no endereço 0x{endereco:05X} (linha {num_linha})"
                )

            bus.store_word(endereco, instrucao)
            endereco += 4

    return endereco_inicial
