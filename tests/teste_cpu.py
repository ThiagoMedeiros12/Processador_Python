import pytest
from memoria.ram import RAM
from devices.vram import VRAM
from memoria.bus import Bus
from cpu.processor import CPU


@pytest.fixture
def ambiente_cpu():
    ram = RAM(0x80000)
    vram = VRAM(0x10000)
    bus = Bus(ram, vram)
    cpu = CPU(bus)
    return cpu, bus, ram, vram


def test_cpu_acesso_vram_via_bus(ambiente_cpu):
    cpu, bus, _, vram = ambiente_cpu

    # Programa: escreve 0xAB no endereco absoluto 0x80010 (VRAM local 0x10)
    programa = [
        0x000800B7,  # lui  x1, 0x80       (x1 = 0x80000)
        0x0AB00113,  # addi x2, x0, 0xAB   (x2 = 0xAB)
        0x00208823,  # sb   x2, 0x10(x1)   (bus.store_byte(0x80010, 0xAB))
        0x0100C183,  # lbu  x3, 0x10(x1)   (x3 = bus.load_byte(0x80010))
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert vram.load_byte(0x10) == 0xAB
    assert cpu.ler_registrador(3) == 0xAB
    assert cpu.ler_registrador(0) == 0
    
def test_cpu_executa_clz(ambiente_cpu):
    cpu, bus, _, _ = ambiente_cpu

    programa = [
        0x00500113,  # addi x2, x0, 5
        0x60011193,  # clz  x3, x2
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert cpu.ler_registrador(2) == 5
    assert cpu.ler_registrador(3) == 29
    
    
def test_cpu_executa_add(ambiente_cpu):

    cpu, bus, _, _ = ambiente_cpu

    programa = [
        0x00500113,  # addi x2, x0, 5
        0x00300193,  # addi x3, x0, 3
        0x00310233,  # add  x4, x2, x3
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert cpu.ler_registrador(2) == 5
    assert cpu.ler_registrador(3) == 3
    assert cpu.ler_registrador(4) == 8


def test_cpu_clz_zero(ambiente_cpu):

    cpu, bus, _, _ = ambiente_cpu

    programa = [
        0x00000113,  # addi x2, x0, 0
        0x60011193,  # clz x3, x2
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert cpu.ler_registrador(3) == 32


def test_cpu_clz_msb(ambiente_cpu):

    cpu, bus, _, _ = ambiente_cpu

    programa = [
        0x80000137,  # lui x2, 0x80000
        0x60011193,  # clz x3, x2
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert cpu.ler_registrador(3) == 0


def test_cpu_registrador_x31(ambiente_cpu):

    cpu, bus, _, _ = ambiente_cpu

    programa = [
        0x02A00F93,  # addi x31, x0, 42
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert cpu.ler_registrador(31) == 42

def test_cpu_utiliza_register_file(ambiente_cpu):
    cpu, _, _, _ = ambiente_cpu

    cpu.escrever_registrador(5, 123)

    assert cpu.register_file.read(5) == 123
    assert cpu.ler_registrador(5) == 123
    assert cpu.registradores is cpu.register_file.values
    
def test_cpu_preserva_x0_com_register_file(ambiente_cpu):
    cpu, _, _, _ = ambiente_cpu

    cpu.escrever_registrador(0, 999)

    assert cpu.register_file.read(0) == 0
    assert cpu.ler_registrador(0) == 0
    
def test_cpu_envia_caractere_para_terminal(ambiente_cpu):

    from devices.terminal import Terminal

    cpu, bus, _, _ = ambiente_cpu
    terminal = Terminal(bus.io_device)

    programa = [
        0x000A00B7,  # lui x1, 0xA0
        0xC0008093,  # addi x1, x1, -1024 -> 0x9FC00
        0x04100113,  # addi x2, x0, 65 ('A')
        0x00208223,  # sb x2, 4(x1) -> DATA_OUT
        0x00100073,  # ebreak
    ]

    for i, instrucao in enumerate(programa):
        bus.store_word(i * 4, instrucao)

    cpu.executar()

    assert terminal.obter_saida() == "A"


def test_cpu_executa_arquivo_clz_test(ambiente_cpu):
    from programs.loader import carregar_programa

    cpu, bus, _, _ = ambiente_cpu
    carregar_programa("programs/clz_test.hex", bus)
    ciclos = cpu.executar()

    assert ciclos > 0
    assert cpu.ler_registrador(2) == 32
    assert cpu.ler_registrador(4) == 29
    assert cpu.ler_registrador(6) == 0
    assert cpu.ler_registrador(8) == 31
    assert bus.load_word(0x100) == 32
    assert bus.load_word(0x104) == 29
    assert bus.load_word(0x108) == 0
    assert bus.load_word(0x10C) == 31


def test_cpu_executa_arquivo_system_test(ambiente_cpu):
    from programs.loader import carregar_programa
    from devices.terminal import Terminal

    cpu, bus, _, vram = ambiente_cpu
    terminal = Terminal(bus.io_device)

    carregar_programa("programs/system_test.hex", bus)
    ciclos = cpu.executar()

    assert ciclos > 0
    assert terminal.obter_saida() == "RISC-V OK!\n"
    assert vram.load_byte(0) == ord("+")
    assert vram.load_byte(1) == ord("-")


def test_cpu_ciclo_interrupcao_e_mret(ambiente_cpu):
    cpu, bus, _, _ = ambiente_cpu

    # Programa principal:
    # 0x00: addi x1, x0, 10
    # 0x04: addi x2, x0, 20
    # 0x08: ebreak
    bus.store_word(0x00, 0x00A00093)
    bus.store_word(0x04, 0x01400113)
    bus.store_word(0x08, 0x00100073)

    # Tratador de Interrupção (ISR) em 0x00040:
    # 0x40: addi x3, x0, 99 (marca execução da ISR)
    # 0x44: mret (retorna da interrupção para o PC salvo)
    bus.store_word(0x40, 0x06300193)
    bus.store_word(0x44, 0x30200073)  # mret

    # Executa primeiro ciclo (addi x1, x0, 10)
    cpu.executar_ciclo()
    assert cpu.ler_registrador(1) == 10

    # Dispara interrupção externa no barramento
    bus.solicitar_interrupcao(codigo=1)

    # Executa segundo ciclo: CPU executa 0x04 (addi x2, x0, 20) e atende a interrupção saltando para 0x40
    cpu.executar_ciclo()
    assert cpu.ler_registrador(2) == 20
    assert cpu.pc == 0x40
    assert cpu.mepc == 0x08
    assert cpu.interrupcoes_processadas == 1

    # Executa o tratador de interrupção
    cpu.executar_ciclo()  # addi x3, x0, 99
    assert cpu.ler_registrador(3) == 99

    cpu.executar_ciclo()  # mret -> retorna para 0x08
    assert cpu.pc == 0x08
    assert cpu.interrupcoes_habilitadas is True

    # Continua o programa principal (ebreak)
    cpu.executar_ciclo()
    assert cpu.rodando is False


def test_cpu_executa_arquivo_sistema_completo(ambiente_cpu):
    from programs.loader import carregar_programa
    from devices.terminal import Terminal

    cpu, bus, _, vram = ambiente_cpu
    terminal = Terminal(bus.io_device)

    carregar_programa("programs/sistema_completo.hex", bus)
    ciclos = cpu.executar()

    assert ciclos > 0
    assert terminal.obter_saida() == "[RV32I] SISTEMA COMPLETO OK\n"
    assert bus.load_word(0x240) == 31
    assert bus.load_word(0x244) == 30
    assert bus.load_word(0x248) == 29
    assert bus.load_word(0x24C) == 28
    assert vram.load_byte(0) == ord("+")
    assert vram.load_byte(1) == ord("-")


