#!/usr/bin/env python3
"""
Simulador de Processador RISC-V (RV32I + Zbb CLZ)
Interface de Linha de Comando (CLI)
"""

import sys
import argparse
from memoria.bus import Bus
from memoria.cache import CacheMMU
from cpu.processor import CPU
from cpu.decoder import Decoder
from devices.terminal import Terminal
from devices.vram_viewer import VRAMViewer
from programs.loader import carregar_programa

NOMES_ABI = [
    "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
    "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
    "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
    "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
]


def desassembilar(inst):
    op = inst["operacao"]
    tipo = inst["tipo"]
    rd = f"x{inst['rd']}"
    rs1 = f"x{inst['rs1']}"
    rs2 = f"x{inst['rs2']}"
    imm = inst["imm"]

    if tipo == "R":
        return f"{op:<7} {rd}, {rs1}, {rs2}"
    elif tipo == "I":
        if op == "CLZ":
            return f"{op:<7} {rd}, {rs1}"
        return f"{op:<7} {rd}, {rs1}, {imm}"
    elif tipo == "S":
        return f"{op:<7} {rs2}, {imm}({rs1})"
    elif tipo == "B":
        return f"{op:<7} {rs1}, {rs2}, {imm}"
    elif tipo == "U":
        return f"{op:<7} {rd}, 0x{imm:X}"
    elif tipo == "J":
        return f"{op:<7} {rd}, {imm}"
    elif tipo == "SYS":
        return f"{op}"
    return f"{op}"


def formatar_registradores(cpu):
    linhas = [
        "=" * 72,
        f"  ESTADO DOS REGISTRADORES (PC: 0x{cpu.pc:08X})",
        "=" * 72,
    ]
    for row in range(8):
        partes = []
        for col in range(4):
            idx = row + col * 8
            val = cpu.ler_registrador(idx)
            partes.append(f"x{idx:<2} ({NOMES_ABI[idx]:<4}): 0x{val:08X}")
        linhas.append("  " + "  |  ".join(partes))
    linhas.append("=" * 72)
    return "\n".join(linhas)


def executar_simulador(args):
    bus = Bus()
    decoder = Decoder()
    terminal = Terminal(bus.io_device)

    # Converte PC inicial e RAM inicial se forem strings hex
    pc_inicial = int(args.pc, 16) if isinstance(args.pc, str) and args.pc.startswith(("0x", "0X")) else int(args.pc)
    ram_inicio = int(args.ram_inicio, 16) if isinstance(args.ram_inicio, str) and args.ram_inicio.startswith(("0x", "0X")) else int(args.ram_inicio)

    print(f"\n[+] Carregando programa: {args.arquivo}")
    try:
        carregar_programa(args.arquivo, bus, endereco_inicial=pc_inicial)
    except Exception as e:
        print(f"[!] Erro ao carregar programa: {e}", file=sys.stderr)
        return 1

    if args.entrada:
        terminal.enviar_entrada(args.entrada)

    # Se a flag --cache estiver ativa, instancia a CacheMMU de 256 linhas (Ponto Extra 1)
    cache = None
    if args.cache:
        print(f"[+] Ativando Memória Cache de 256 linhas ({args.cache_vias} via(s))...")
        cache = CacheMMU(bus, total_linhas=256, vias=args.cache_vias)
        cpu = CPU(cache, pc_inicial=pc_inicial)
    else:
        cpu = CPU(bus, pc_inicial=pc_inicial)

    ciclos = 0
    modo_passo = args.step

    print(f"[+] Iniciando execução a partir de PC=0x{cpu.pc:08X}...")
    if modo_passo:
        print("[*] Modo interativo ativado. Digite 'help' ou '?' para ver todos os comandos.")

    viewer = VRAMViewer(
        bus.vram,
        largura=args.vram_largura,
        altura=args.vram_altura,
        modo=args.vram_modo
    )

    while cpu.rodando and ciclos < args.max_ciclos:
        pc_atual = cpu.pc
        try:
            instrucao_bruta = cpu.buscar()
            inst = decoder.decodificar(instrucao_bruta)
            disasm = desassembilar(inst)
        except Exception as e:
            print(f"\n[!] Falha ao buscar/decodificar no PC=0x{pc_atual:08X}: {e}", file=sys.stderr)
            break

        if modo_passo:
            prompt = f"[{ciclos:05d}] PC: 0x{pc_atual:08X} | 0x{instrucao_bruta:08X}  {disasm} > "
            try:
                cmd_raw = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[!] Execução interrompida pelo usuário.")
                break

            cmd = cmd_raw.lower()
            tokens = cmd_raw.split()

            if cmd in ("q", "quit", "exit"):
                print("[*] Encerrando pelo comando de saída.")
                break
            elif cmd in ("help", "?"):
                print("\n" + "=" * 64)
                print("  COMANDOS DO MODO INTERATIVO (Seção Pontuação Extra 3)")
                print("=" * 64)
                print("  [Enter] / s               : Executa 1 instrução (passo)")
                print("  c                         : Continua execução sem pausar")
                print("  r                         : Exibe os 32 registradores")
                print("  m                         : Exibe a matriz de 32 colunas da RAM")
                print("  v                         : Exibe a VRAM em arte ASCII")
                print("  int                       : Dispara interrupção de hardware no barramento")
                print("  tecla <caractere>         : Injeta caractere via teclado e gera INT")
                print("  set r <reg> <val>         : Altera registrador (ex: set r x1 42 ou set r 2 0x100)")
                print("  set m <end> <val>         : Altera palavra na RAM (ex: set m 0x200 0x12345678)")
                print("  load <hex> [end]          : Grava instrução no PC atual ou endereço especificado")
                print("  goto <end>                : Modifica o PC para outro endereço")
                print("  q                         : Encerra a simulação")
                print("=" * 64 + "\n")
                continue
            elif cmd in ("c", "cont"):
                modo_passo = False
            elif cmd == "r":
                print(formatar_registradores(cpu))
                continue
            elif cmd == "m":
                print(bus.ram.dump_matriz_32_colunas(endereco_inicial=ram_inicio, num_linhas=args.ram_linhas))
                continue
            elif cmd == "v":
                viewer.exibir()
                continue
            elif cmd == "int":
                bus.solicitar_interrupcao(codigo=1)
                print("[*] Interrupção externa requisitada no barramento!")
                continue
            elif len(tokens) >= 2 and tokens[0].lower() == "tecla":
                char = tokens[1][0]
                terminal.enviar_entrada(char)
                print(f"[✓] Tecla '{char}' enviada! Interrupção de hardware de teclado gerada.")
                continue
            elif len(tokens) >= 4 and tokens[0].lower() == "set" and tokens[1].lower() == "r":
                reg_str = tokens[2].lower().replace("x", "")
                val_str = tokens[3]
                try:
                    reg_idx = int(reg_str)
                    val = int(val_str, 16) if val_str.startswith(("0x", "0X")) else int(val_str)
                    cpu.escrever_registrador(reg_idx, val)
                    print(f"[✓] Registrador x{reg_idx} atualizado para 0x{val & 0xFFFFFFFF:08X} ({val})")
                except Exception as ex:
                    print(f"[!] Erro ao alterar registrador: {ex}")
                continue
            elif len(tokens) >= 4 and tokens[0].lower() == "set" and tokens[1].lower() == "m":
                end_str = tokens[2]
                val_str = tokens[3]
                try:
                    end_val = int(end_str, 16) if end_str.startswith(("0x", "0X")) else int(end_str)
                    val = int(val_str, 16) if val_str.startswith(("0x", "0X")) else int(val_str)
                    bus.store_word(end_val, val)
                    print(f"[✓] Memória RAM[0x{end_val:05X}] atualizada para 0x{val & 0xFFFFFFFF:08X}")
                except Exception as ex:
                    print(f"[!] Erro ao alterar memória: {ex}")
                continue
            elif len(tokens) >= 2 and tokens[0].lower() == "load":
                inst_hex = tokens[1]
                end_dest = pc_atual if len(tokens) < 3 else (int(tokens[2], 16) if tokens[2].startswith(("0x", "0X")) else int(tokens[2]))
                try:
                    inst_val = int(inst_hex, 16)
                    bus.store_word(end_dest, inst_val)
                    dec = decoder.decodificar(inst_val)
                    print(f"[✓] Instrução 0x{inst_val:08X} gravada em 0x{end_dest:08X} ({desassembilar(dec)})")
                except Exception as ex:
                    print(f"[!] Erro ao gravar instrução: {ex}")
                continue
            elif len(tokens) >= 2 and tokens[0].lower() == "goto":
                try:
                    novo_pc = int(tokens[1], 16) if tokens[1].startswith(("0x", "0X")) else int(tokens[1])
                    cpu.pc = novo_pc & 0xFFFFFFFF
                    print(f"[✓] PC alterado para 0x{cpu.pc:08X}")
                except Exception as ex:
                    print(f"[!] Erro ao alterar PC: {ex}")
                continue
        elif args.debug:
            print(f"[{ciclos:05d}] PC: 0x{pc_atual:08X} | 0x{instrucao_bruta:08X}  {disasm}")

        cpu.executar_ciclo()
        ciclos += 1

        # Transmite saída pendente do Terminal
        saida_pendente = terminal.obter_saida()
        if saida_pendente:
            print(saida_pendente, end="", flush=True)

        # Transmissão periódica da VRAM a cada n instruções (Seção 4 do edital)
        if args.vram_intervalo > 0 and (ciclos % args.vram_intervalo == 0):
            print(f"\n--- [Transmissão de VRAM a cada {args.vram_intervalo} instruções | Ciclo {ciclos}] ---")
            viewer.exibir()

    # Se a cache estiver ativa, descarrega blocos sujos (flush)
    if cache is not None:
        cache.flush()

    print(f"\n[+] Execução finalizada após {ciclos} ciclos.")
    print(f"[+] PC final: 0x{cpu.pc:08X} | CPU rodando: {cpu.rodando}")

    if args.dump_regs:
        print("\n" + formatar_registradores(cpu))

    if args.dump_ram:
        print("\n" + bus.ram.dump_matriz_32_colunas(
            endereco_inicial=ram_inicio,
            num_linhas=args.ram_linhas,
            omitir_vazias=args.ram_omitir_vazias
        ))

    if args.vram and (args.vram_intervalo == 0 or ciclos % args.vram_intervalo != 0):
        print("\n[+] Exibição da VRAM final (ASCII):")
        viewer.exibir()

    if cache is not None:
        print("\n" + cache.relatorio_estatisticas())

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Simulador de CPU RISC-V RV32I + Zbb (CLZ) com barramento, periféricos e VRAM ASCII."
    )
    parser.add_argument("arquivo", help="Caminho do arquivo .hex contendo as instruções do programa.")
    parser.add_argument("--pc", default="0x00000", help="PC inicial da CPU (padrão: 0x00000).")
    parser.add_argument("--max-ciclos", type=int, default=10000, help="Limite máximo de ciclos a executar (padrão: 10000).")
    parser.add_argument("-s", "--step", action="store_true", help="Executa passo-a-passo interativamente.")
    parser.add_argument("-d", "--debug", action="store_true", help="Imprime o desmonte de cada instrução em tempo de execução.")
    parser.add_argument("--dump-regs", action="store_true", help="Imprime o mapa completo de registradores ao final.")
    parser.add_argument("--vram", action="store_true", help="Renderiza a VRAM em arte ASCII no terminal ao final.")
    parser.add_argument("--vram-intervalo", type=int, default=0, help="Intervalo de instruções para transmissão periódica da VRAM (Seção 4 do edital).")
    parser.add_argument("--vram-largura", type=int, default=16, help="Largura da visualização da VRAM (padrão: 16).")
    parser.add_argument("--vram-altura", type=int, default=8, help="Altura da visualização da VRAM (padrão: 8).")
    parser.add_argument("--vram-modo", default="auto", choices=["auto", "char", "pixel"], help="Modo de renderização da VRAM: auto, char ou pixel.")
    parser.add_argument("--dump-ram", action="store_true", help="Imprime a memória RAM formatada em matriz de 32 colunas (Seção 3 do edital).")
    parser.add_argument("--ram-inicio", default="0x00000", help="Endereço inicial para o dump da RAM (padrão: 0x00000).")
    parser.add_argument("--ram-linhas", type=int, default=8, help="Número de linhas (de 32 colunas cada) a exibir no dump da RAM.")
    parser.add_argument("--ram-omitir-vazias", action="store_true", help="Omite linhas zeradas no dump da RAM.")
    parser.add_argument("--cache", action="store_true", help="Ativa a memória cache de 256 linhas com MMU (Seção Pontuação Extra 1).")
    parser.add_argument("--cache-vias", type=int, default=1, choices=[1, 2, 4], help="Número de vias da cache (1=Direto, 2=2-way LRU, 4=4-way LRU).")
    parser.add_argument("-i", "--entrada", default="", help="Envia texto de entrada inicial para o I/O da CPU.")

    args = parser.parse_args()
    sys.exit(executar_simulador(args))


if __name__ == "__main__":
    main()
