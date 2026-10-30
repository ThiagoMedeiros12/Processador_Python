from memoria.ram import RAM

def testar_ram():
    # Cria uma RAM com 1024 bytes para o teste
    tamanho_teste = 1024
    ram = RAM(tamanho_teste)
    
    print("Iniciando testes de memória (RAM)...")

    # 1. Teste de escrita e leitura de bytes individuais
    ram.store_byte(0x00, 0x4F) # 'O' em ASCII
    ram.store_byte(0x01, 0x49) # 'I' em ASCII
    
    assert ram.load_byte(0x00) == 0x4F, "Erro no byte 0x00"
    assert ram.load_byte(0x01) == 0x49, "Erro no byte 0x01"
    print(" [OK] Teste de bytes individuais passou!")

    # 2. Teste de escrita e leitura de palavras de 32 bits (Little-Endian)
    # Palavra de exemplo: 0x12345678
    # Em little-endian, o byte menos significativo (0x78) fica no menor endereço.
    endereco_palavra = 0x04
    valor_original = 0x12345678
    
    ram.store_word(endereco_palavra, valor_original)
    
    # Verifica se os bytes foram posicionados na ordem correta na memória física
    assert ram.load_byte(endereco_palavra) == 0x78
    assert ram.load_byte(endereco_palavra + 1) == 0x56
    assert ram.load_byte(endereco_palavra + 2) == 0x34
    assert ram.load_byte(endereco_palavra + 3) == 0x12
    
    # Verifica se a recuperação da palavra inteira funciona
    valor_lido = ram.load_word(endereco_palavra)
    assert valor_lido == valor_original, f" esperado {hex(valor_original)}, obtido {hex(valor_lido)}"
    print(" [OK] Teste de palavras (load_word / store_word) passou!")

    # 3. Teste de restrição de alinhamento para palavras
    # Endereços de 32 bits devem ser múltiplos de 4 (endereço 0x05 não é alinhado)
    try:
        ram.load_word(0x05)
        assert False, "Deveria ter lançado um erro de alinhamento!"
    except ValueError:
        print(" [OK] Teste de erro para endereço não alinhado passou!")

    print("\nTodos os testes da RAM passaram com sucesso!")

if __name__ == "__main__":
    testar_ram()