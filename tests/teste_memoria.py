
from memoria.ram import RAM, VRAM


def testar_ram():
    # Cria uma RAM com 1024 bytes para o teste
    tamanho_teste = 1024
    ram = RAM(tamanho_teste)

    print("Iniciando testes de memória (RAM)...")

    # 1. Teste de escrita e leitura de bytes individuais
    ram.store_byte(0x00, 0x4F)  # 'O' em ASCII
    ram.store_byte(0x01, 0x49)  # 'I' em ASCII

    assert ram.load_byte(0x00) == 0x4F, "Erro no byte 0x00"
    assert ram.load_byte(0x01) == 0x49, "Erro no byte 0x01"

    print(" [OK] Teste de bytes individuais passou!")

    # 2. Teste de escrita e leitura de palavras de 32 bits
    # Little-endian: byte menos significativo no menor endereco
    endereco_palavra = 0x04
    valor_original = 0x12345678

    ram.store_word(endereco_palavra, valor_original)

    # Verifica os bytes na memoria
    assert ram.load_byte(endereco_palavra) == 0x78
    assert ram.load_byte(endereco_palavra + 1) == 0x56
    assert ram.load_byte(endereco_palavra + 2) == 0x34
    assert ram.load_byte(endereco_palavra + 3) == 0x12

    # Verifica leitura da palavra inteira
    valor_lido = ram.load_word(endereco_palavra)

    assert valor_lido == valor_original, (
        f"Esperado {hex(valor_original)}, "
        f"obtido {hex(valor_lido)}"
    )

    print(" [OK] Teste de palavras (load_word / store_word) passou!")

    # 3. Teste de alinhamento
    try:
        ram.load_word(0x05)
        assert False, "Deveria ter lançado erro de alinhamento!"
    except ValueError as erro:
        assert "alinhado" in str(erro).lower()

    print(" [OK] Teste de alinhamento passou!")

    # 4. Teste de endereco fora da RAM
    try:
        ram.load_byte(1024)
        assert False, "Deveria ter lançado erro de endereço!"
    except ValueError as erro:
        assert "ram" in str(erro).lower()

    print(" [OK] Teste de endereço fora da RAM passou!")

    # 5. Teste de endereço negativo
    try:
        ram.load_byte(-1)
        assert False, "Deveria ter lançado erro para endereço negativo!"
    except ValueError:
        pass

    print(" [OK] Teste de endereço negativo passou!")

    # 6. Teste de endereço que não é inteiro
    try:
        ram.load_byte("10")
        assert False, "Deveria ter lançado TypeError!"
    except TypeError:
        pass

    print(" [OK] Teste de tipo de endereço passou!")

    # 7. Teste de word no limite da RAM
    # 1020 é válido: acessa 1020, 1021, 1022 e 1023
    ram.store_word(1020, 0xAABBCCDD)

    assert ram.load_word(1020) == 0xAABBCCDD

    print(" [OK] Teste de word no limite válido passou!")

    # 8. Teste de word que ultrapassa a RAM
    # 1024 está fora da RAM e não pode ser acessado
    try:
        ram.store_word(1024, 0x12345678)
        assert False, "Deveria ter lançado erro de limite!"
    except ValueError:
        pass

    # 1022 é alinhado? Não. O erro esperado aqui é de alinhamento.
    try:
        ram.load_word(1022)
        assert False, "Deveria ter lançado erro de alinhamento!"
    except ValueError:
        pass

    print(" [OK] Teste de limite de word passou!")

    print("\nTodos os testes da RAM passaram com sucesso!")

def testar_vram():

    # VRAM possui 64 KiB = 0x10000 bytes
    tamanho_teste = 0x10000

    vram = VRAM(tamanho_teste)

    print("Iniciando testes de memória (VRAM)...")

    # 1. Teste de tamanho da VRAM
    assert len(vram.bytes) == 0x10000

    print(" [OK] Teste de tamanho da VRAM passou!")

    # 2. Teste de escrita e leitura de bytes individuais
    vram.store_byte(0x00, 0x4F)  # 'O'
    vram.store_byte(0x01, 0x49)  # 'I'

    assert vram.load_byte(0x00) == 0x4F
    assert vram.load_byte(0x01) == 0x49

    print(" [OK] Teste de bytes individuais passou!")

    # 3. Teste de escrita e leitura em endereco intermediario
    endereco = 0x1000
    valor = 0xAB

    vram.store_byte(endereco, valor)

    assert vram.load_byte(endereco) == valor

    print(" [OK] Teste de endereco intermediario passou!")

    # 4. Teste do ultimo endereco valido
    ultimo_endereco = 0xFFFF

    vram.store_byte(ultimo_endereco, 0xFF)

    assert vram.load_byte(ultimo_endereco) == 0xFF

    print(" [OK] Teste do ultimo endereco valido passou!")

    # 5. Teste de endereco fora da VRAM
    try:
        vram.load_byte(0x10000)

        assert False, (
            "Deveria ter lançado erro para "
            "endereco fora da VRAM!"
        )

    except ValueError as erro:
        assert "vram" in str(erro).lower()

    print(" [OK] Teste de endereco fora da VRAM passou!")

    # 6. Teste de endereco negativo
    try:
        vram.load_byte(-1)

        assert False, (
            "Deveria ter lançado erro "
            "para endereco negativo!"
        )

    except ValueError:
        pass

    print(" [OK] Teste de endereco negativo passou!")

    # 7. Teste de endereco que nao e inteiro
    try:
        vram.load_byte("10")

        assert False, (
            "Deveria ter lançado TypeError "
            "para endereco nao inteiro!"
        )

    except TypeError:
        pass

    print(" [OK] Teste de tipo de endereco passou!")

    # 8. Teste de valor maior que um byte
    vram.store_byte(0x10, 0x1234)

    assert vram.load_byte(0x10) == 0x34

    print(" [OK] Teste de valor de byte passou!")

    print("\nTodos os testes da VRAM passaram com sucesso!")



if __name__ == "__main__":
    testar_ram()
    testar_vram()