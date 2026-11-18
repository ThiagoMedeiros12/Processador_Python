def estender_sinal(valor, bits):
    sinal = 1 << (bits - 1)
    return (valor & (sinal - 1)) - (valor & sinal)


class Decoder:
    def decodificar(self, instrucao):
        if isinstance(instrucao, bool) or not isinstance(instrucao, int):
            raise TypeError("Instrucao precisa ser inteiro")

        instrucao &= 0xFFFFFFFF
        opcode = instrucao & 0x7F
        rd = (instrucao >> 7) & 0x1F
        funct3 = (instrucao >> 12) & 0x7
        rs1 = (instrucao >> 15) & 0x1F
        rs2 = (instrucao >> 20) & 0x1F
        funct7 = (instrucao >> 25) & 0x7F

        # Tipo R (ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU)
        if opcode == 0x33:
            mapa_r = {
                (0x0, 0x00): "ADD",
                (0x0, 0x20): "SUB",
                (0x1, 0x00): "SLL",
                (0x2, 0x00): "SLT",
                (0x3, 0x00): "SLTU",
                (0x4, 0x00): "XOR",
                (0x5, 0x00): "SRL",
                (0x5, 0x20): "SRA",
                (0x6, 0x00): "OR",
                (0x7, 0x00): "AND",
            }
            operacao = mapa_r.get((funct3, funct7))
            if operacao is None:
                raise ValueError("Instrucao Tipo-R desconhecida")
            return {
                "tipo": "R",
                "operacao": operacao,
                "rd": rd,
                "rs1": rs1,
                "rs2": rs2,
                "imm": 0,
            }

        # Tipo I - ALU (ADDI, ANDI, ORI, XORI, SLTI, SLTIU, SLLI, SRLI, SRAI)
        if opcode == 0x13:
            imm = estender_sinal((instrucao >> 20) & 0xFFF, 12)
            shamt = (instrucao >> 20) & 0x1F

            if funct3 == 0x0:
                operacao = "ADDI"
            elif funct3 == 0x2:
                operacao = "SLTI"
            elif funct3 == 0x3:
                operacao = "SLTIU"
            elif funct3 == 0x4:
                operacao = "XORI"
            elif funct3 == 0x6:
                operacao = "ORI"
            elif funct3 == 0x7:
                operacao = "ANDI"
            elif funct3 == 0x1 and ((instrucao >> 20) & 0xFFF) == 0x600:
                operacao = "CLZ"
                imm = 0
            elif funct3 == 0x1 and funct7 == 0x00:
                operacao = "SLLI"
                imm = shamt
            elif funct3 == 0x5 and funct7 == 0x00:
                operacao = "SRLI"
                imm = shamt
            elif funct3 == 0x5 and funct7 == 0x20:
                operacao = "SRAI"
                imm = shamt
            else:
                raise ValueError("Instrucao Tipo-I desconhecida")

            return {
                "tipo": "I",
                "operacao": operacao,
                "rd": rd,
                "rs1": rs1,
                "rs2": 0,
                "imm": imm,
            }

        # Tipo I - Load (LB, LW, LBU)
        if opcode == 0x03:
            imm = estender_sinal((instrucao >> 20) & 0xFFF, 12)
            mapa_load = {
                0x0: "LB",
                0x2: "LW",
                0x4: "LBU",
            }
            operacao = mapa_load.get(funct3)
            if operacao is None:
                raise ValueError("Instrucao Load nao suportada")
            return {
                "tipo": "I",
                "operacao": operacao,
                "rd": rd,
                "rs1": rs1,
                "rs2": 0,
                "imm": imm,
            }

        # Tipo I - JALR
        if opcode == 0x67:
            if funct3 != 0x0:
                raise ValueError("Instrucao JALR invalida")
            imm = estender_sinal((instrucao >> 20) & 0xFFF, 12)
            return {
                "tipo": "I",
                "operacao": "JALR",
                "rd": rd,
                "rs1": rs1,
                "rs2": 0,
                "imm": imm,
            }

        # Tipo S - Store (SB, SW)
        if opcode == 0x23:
            imm_bruto = ((instrucao >> 25) << 5) | ((instrucao >> 7) & 0x1F)
            imm = estender_sinal(imm_bruto, 12)
            mapa_store = {
                0x0: "SB",
                0x2: "SW",
            }
            operacao = mapa_store.get(funct3)
            if operacao is None:
                raise ValueError("Instrucao Store nao suportada")
            return {
                "tipo": "S",
                "operacao": operacao,
                "rd": 0,
                "rs1": rs1,
                "rs2": rs2,
                "imm": imm,
            }

        # Tipo B - Branch (BEQ, BNE, BLT, BGE, BLTU, BGEU)
        if opcode == 0x63:
            imm_bruto = (
                (((instrucao >> 31) & 0x1) << 12)
                | (((instrucao >> 7) & 0x1) << 11)
                | (((instrucao >> 25) & 0x3F) << 5)
                | (((instrucao >> 8) & 0xF) << 1)
            )
            imm = estender_sinal(imm_bruto, 13)
            mapa_branch = {
                0x0: "BEQ",
                0x1: "BNE",
                0x4: "BLT",
                0x5: "BGE",
                0x6: "BLTU",
                0x7: "BGEU",
            }
            operacao = mapa_branch.get(funct3)
            if operacao is None:
                raise ValueError("Instrucao Branch nao suportada")
            return {
                "tipo": "B",
                "operacao": operacao,
                "rd": 0,
                "rs1": rs1,
                "rs2": rs2,
                "imm": imm,
            }

        # Tipo U (LUI, AUIPC)
        if opcode in (0x37, 0x17):
            imm = instrucao & 0xFFFFF000
            operacao = "LUI" if opcode == 0x37 else "AUIPC"
            return {
                "tipo": "U",
                "operacao": operacao,
                "rd": rd,
                "rs1": 0,
                "rs2": 0,
                "imm": imm,
            }

        # Tipo J (JAL)
        if opcode == 0x6F:
            imm_bruto = (
                (((instrucao >> 31) & 0x1) << 20)
                | (((instrucao >> 12) & 0xFF) << 12)
                | (((instrucao >> 20) & 0x1) << 11)
                | (((instrucao >> 21) & 0x3FF) << 1)
            )
            imm = estender_sinal(imm_bruto, 21)
            return {
                "tipo": "J",
                "operacao": "JAL",
                "rd": rd,
                "rs1": 0,
                "rs2": 0,
                "imm": imm,
            }

        # Sistema (EBREAK, ECALL, MRET)
        if opcode == 0x73:
            imm = (instrucao >> 20) & 0xFFF
            if imm == 1:
                operacao = "EBREAK"
            elif imm == 0x302:
                operacao = "MRET"
            else:
                operacao = "ECALL"

            return {
                "tipo": "SYS",
                "operacao": operacao,
                "rd": 0,
                "rs1": 0,
                "rs2": 0,
                "imm": imm,
            }

        raise ValueError("Opcode desconhecido")