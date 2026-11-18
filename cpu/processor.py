
from memoria.bus import Bus
from cpu.decoder import Decoder, estender_sinal
from cpu.alu import clz32
from cpu.registrador import RegisterFile

MASK32 = 0xFFFFFFFF


class CPU:

    def __init__(self, bus=None, pc_inicial=0x00000):
        self.bus = bus if bus is not None else Bus()
        self.decoder = Decoder()

        # Banco de registradores da CPU
        self.register_file = RegisterFile()

        # Compatibilidade com códigos antigos que acessam registradores
        self.registradores = self.register_file.values

        self.pc = pc_inicial & MASK32
        self.rodando = True

    def ler_registrador(self, indice):
        return self.register_file.read(indice)


    def escrever_registrador(self, indice, valor):
        self.register_file.write(indice, valor)

    def buscar(self):
        return self.bus.load_word(self.pc)

    def executar_ciclo(self):

        if not self.rodando:
            return

        instrucao_bruta = self.buscar()
        inst = self.decoder.decodificar(instrucao_bruta)

        proximo_pc = (self.pc + 4) & MASK32

        op = inst["operacao"]
        rd = inst["rd"]
        rs1 = inst["rs1"]
        rs2 = inst["rs2"]
        imm = inst["imm"]

        v1 = self.ler_registrador(rs1)
        v2 = self.ler_registrador(rs2)

        s1 = estender_sinal(v1, 32)
        s2 = estender_sinal(v2, 32)

        # =========================
        # TIPO R
        # =========================

        if op == "ADD":
            self.escrever_registrador(rd, v1 + v2)

        elif op == "SUB":
            self.escrever_registrador(rd, v1 - v2)

        elif op == "SLL":
            self.escrever_registrador(rd, v1 << (v2 & 0x1F))

        elif op == "SLT":
            self.escrever_registrador(rd, int(s1 < s2))

        elif op == "SLTU":
            self.escrever_registrador(rd, int(v1 < v2))

        elif op == "XOR":
            self.escrever_registrador(rd, v1 ^ v2)

        elif op == "SRL":
            self.escrever_registrador(rd, v1 >> (v2 & 0x1F))

        elif op == "SRA":
            self.escrever_registrador(rd, s1 >> (v2 & 0x1F))

        elif op == "OR":
            self.escrever_registrador(rd, v1 | v2)

        elif op == "AND":
            self.escrever_registrador(rd, v1 & v2)

        # =========================
        # TIPO I - ALU
        # =========================

        elif op == "CLZ":
            self.escrever_registrador(rd, clz32(v1))

        elif op == "ADDI":
            self.escrever_registrador(rd, v1 + imm)

        elif op == "SLTI":
            self.escrever_registrador(rd, int(s1 < imm))

        elif op == "SLTIU":
            self.escrever_registrador(
                rd, int(v1 < (imm & MASK32))
            )

        elif op == "XORI":
            self.escrever_registrador(rd, v1 ^ imm)

        elif op == "ORI":
            self.escrever_registrador(rd, v1 | imm)

        elif op == "ANDI":
            self.escrever_registrador(rd, v1 & imm)

        elif op == "SLLI":
            self.escrever_registrador(rd, v1 << imm)

        elif op == "SRLI":
            self.escrever_registrador(rd, v1 >> imm)

        elif op == "SRAI":
            self.escrever_registrador(rd, s1 >> imm)

        # =========================
        # LOAD
        # =========================

        elif op == "LB":
            endereco = (v1 + imm) & MASK32
            valor = self.bus.load_byte(endereco)
            self.escrever_registrador(
                rd, estender_sinal(valor, 8)
            )

        elif op == "LBU":
            endereco = (v1 + imm) & MASK32
            valor = self.bus.load_byte(endereco)
            self.escrever_registrador(rd, valor)

        elif op == "LW":
            endereco = (v1 + imm) & MASK32
            valor = self.bus.load_word(endereco)
            self.escrever_registrador(rd, valor)

        # =========================
        # STORE
        # =========================

        elif op == "SB":
            endereco = (v1 + imm) & MASK32
            self.bus.store_byte(endereco, v2 & 0xFF)

        elif op == "SW":
            endereco = (v1 + imm) & MASK32
            self.bus.store_word(endereco, v2)

        # =========================
        # BRANCH
        # =========================

        elif op == "BEQ":
            if v1 == v2:
                proximo_pc = (self.pc + imm) & MASK32

        elif op == "BNE":
            if v1 != v2:
                proximo_pc = (self.pc + imm) & MASK32

        elif op == "BLT":
            if s1 < s2:
                proximo_pc = (self.pc + imm) & MASK32

        elif op == "BGE":
            if s1 >= s2:
                proximo_pc = (self.pc + imm) & MASK32

        elif op == "BLTU":
            if v1 < v2:
                proximo_pc = (self.pc + imm) & MASK32

        elif op == "BGEU":
            if v1 >= v2:
                proximo_pc = (self.pc + imm) & MASK32

        # =========================
        # UPPER
        # =========================

        elif op == "LUI":
            self.escrever_registrador(rd, imm)

        elif op == "AUIPC":
            self.escrever_registrador(
                rd, self.pc + imm
            )

        # =========================
        # JUMP
        # =========================

        elif op == "JAL":
            self.escrever_registrador(rd, proximo_pc)
            proximo_pc = (self.pc + imm) & MASK32

        elif op == "JALR":
            self.escrever_registrador(rd, proximo_pc)
            proximo_pc = (v1 + imm) & ~1 & MASK32

        # =========================
        # SISTEMA
        # =========================

        elif op in ("EBREAK", "ECALL"):
            self.rodando = False

        else:
            raise NotImplementedError(
                f"Instrucao nao implementada: {op}"
            )

        self.pc = proximo_pc

    def executar(self, limite_ciclos=10000):

        ciclos = 0

        while self.rodando and ciclos < limite_ciclos:
            self.executar_ciclo()
            ciclos += 1

        if self.rodando:
            raise RuntimeError(
                "Limite de ciclos atingido. "
                "Verifique se existe um loop infinito."
            )

        return ciclos
