
from memoria.bus import Bus
from cpu.decoder import Decoder, estender_sinal
from cpu.alu import ALU, clz32
from cpu.registrador import RegisterFile

MASK32 = 0xFFFFFFFF


class CPU:

    def __init__(self, bus=None, pc_inicial=0x00000, endereco_isr=0x00040):
        self.bus = bus if bus is not None else Bus()
        self.decoder = Decoder()

        # Banco de registradores da CPU
        self.register_file = RegisterFile()

        # Compatibilidade com códigos antigos que acessam registradores
        self.registradores = self.register_file.values

        self.pc = pc_inicial & MASK32
        self.rodando = True

        # Controle de interrupções (Figura 7 do edital)
        self.interrupcoes_habilitadas = True
        self.endereco_isr = endereco_isr & MASK32
        self.mepc = 0  # Registrador de retorno de exceção/interrupção
        self.interrupcoes_processadas = 0

    def processar_interrupcao(self):
        """Atende a requisição de interrupção (Figura 7 do edital)."""
        self.mepc = self.pc
        self.interrupcoes_habilitadas = False
        if hasattr(self.bus, "atender_interrupcao"):
            self.bus.atender_interrupcao()
        self.interrupcoes_processadas += 1
        self.pc = self.endereco_isr

    def retornar_interrupcao(self):
        """Retorna da interrupção (instrução MRET)."""
        self.pc = self.mepc & MASK32
        self.interrupcoes_habilitadas = True

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

        if op in ("ADD", "SUB", "SLL", "SLT", "SLTU", "XOR", "SRL", "SRA", "OR", "AND"):
            self.escrever_registrador(rd, ALU.executar(op, v1, v2))

        # =========================
        # TIPO I - ALU
        # =========================

        elif op in ("CLZ", "ADDI", "SLTI", "SLTIU", "XORI", "ORI", "ANDI", "SLLI", "SRLI", "SRAI"):
            self.escrever_registrador(rd, ALU.executar(op, v1, imm))

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

        elif op == "MRET":
            self.retornar_interrupcao()
            proximo_pc = self.pc

        else:
            raise NotImplementedError(
                f"Instrucao nao implementada: {op}"
            )

        self.pc = proximo_pc

        # Ciclo de interrupções (Figura 7 do edital)
        if self.rodando and self.interrupcoes_habilitadas:
            if hasattr(self.bus, "verificar_interrupcao") and self.bus.verificar_interrupcao():
                self.processar_interrupcao()

    def executar(self, limite_ciclos=10000, callback_ciclo=None):

        ciclos = 0

        while self.rodando and ciclos < limite_ciclos:
            self.executar_ciclo()
            ciclos += 1
            if callback_ciclo:
                callback_ciclo(self, ciclos)

        if self.rodando:
            raise RuntimeError(
                "Limite de ciclos atingido. "
                "Verifique se existe um loop infinito."
            )

        return ciclos
