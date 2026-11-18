def carregar_programa(caminho, bus, endereco_inicial=0):

    endereco = endereco_inicial

    with open(caminho, "r", encoding="utf-8") as arquivo:

        for linha in arquivo:

            linha = linha.strip()

            if not linha:
                continue

            instrucao = int(linha, 16)

            bus.store_word(endereco, instrucao)

            endereco += 4

    return endereco_inicial