from functools import wraps

from memoria.ram import RAM
from devices.vram import VRAM
from devices.io import IODevice

from memoria.map_memoria import (
    RAM_INICIO,
    RAM_FIM,
    TAMANHO_RAM,
    VRAM_INICIO,
    VRAM_FIM,
    TAMANHO_VRAM,
    RESERVADO_INICIO,
    RESERVADO_FIM,
    IO_INICIO,
    IO_FIM,
)

def validar_acesso(tamanho_acesso):

    def decorator(func):

        @wraps(func)
        def wrapper(self, endereco, *args, **kwargs):

            if isinstance(endereco, bool) or not isinstance(endereco, int):
                raise TypeError("Endereco precisa ser inteiro")

            if tamanho_acesso == 4 and endereco % 4 != 0:
                raise ValueError("Endereco de palavra nao alinhado")

            if endereco < 0 or endereco > IO_FIM:
                raise ValueError("Endereco fora do mapa de memoria")

            regiao = self._identificar_regiao(endereco)

            final = endereco + tamanho_acesso - 1

            if final > self._fim_regiao(regiao):
                raise ValueError("Acesso ultrapassa limite da regiao")

            if regiao == "RESERVADO":
                raise ValueError("Acesso a memoria reservada")

            return func(self, endereco, *args, **kwargs)

        return wrapper

    return decorator


class Bus:

    def __init__(self, ram=None, vram=None, io_device=None):

        self.ram = ram if ram is not None else RAM(TAMANHO_RAM)

        self.vram = vram if vram is not None else VRAM(TAMANHO_VRAM)

        self.io_device = (
            io_device if io_device is not None else IODevice()
        )
        if hasattr(self.io_device, "vincular_barramento"):
            self.io_device.vincular_barramento(self)

        # 1.) Barramento de dados: 32 bits
        self.barramento_dados = 0

        # 2.) Barramento de endereços: 32 bits
        self.barramento_enderecos = 0

        # 3.) Barramento de controle: leitura/escrita e gerenciamento de interrupções
        self.barramento_controle = {
            "read": False,
            "write": False,
            "tamanho": 1,
            "int_req": False,
            "int_ack": False,
            "int_codigo": 0,
        }

    def solicitar_interrupcao(self, codigo=1):
        """Sinaliza uma requisição de interrupção (INT_REQ) no barramento de controle."""
        self.barramento_controle["int_req"] = True
        self.barramento_controle["int_codigo"] = codigo

    def verificar_interrupcao(self):
        """Verifica se há interrupção pendente na linha de controle do barramento."""
        return self.barramento_controle["int_req"]

    def atender_interrupcao(self):
        """Confirma o atendimento da interrupção (INT_ACK) e limpa a linha de requisição."""
        self.barramento_controle["int_ack"] = True
        self.barramento_controle["int_req"] = False
        return self.barramento_controle["int_codigo"]

    def _identificar_regiao(self, endereco):

        if RAM_INICIO <= endereco <= RAM_FIM:
            return "RAM"

        if VRAM_INICIO <= endereco <= VRAM_FIM:
            return "VRAM"

        if RESERVADO_INICIO <= endereco <= RESERVADO_FIM:
            return "RESERVADO"

        if IO_INICIO <= endereco <= IO_FIM:
            return "IO"

        raise ValueError("Endereco nao pertence a nenhuma regiao")

    def _fim_regiao(self, regiao):

        limites = {
            "RAM": RAM_FIM,
            "VRAM": VRAM_FIM,
            "RESERVADO": RESERVADO_FIM,
            "IO": IO_FIM,
        }

        if regiao not in limites:
            raise ValueError("Regiao desconhecida")

        return limites[regiao]

    def _endereco_local(self, endereco, regiao):

        if regiao == "RAM":
            return endereco - RAM_INICIO

        if regiao == "VRAM":
            return endereco - VRAM_INICIO

        if regiao == "IO":
            return endereco - IO_INICIO

        raise ValueError("Regiao nao possui memoria implementada")

    def _dispositivo(self, regiao):

        if regiao == "RAM":
            return self.ram

        if regiao == "VRAM":
            return self.vram

        if regiao == "IO":
            return self.io_device

        raise ValueError("Regiao sem dispositivo associado")

    @validar_acesso(1)
    def load_byte(self, endereco):
        self.barramento_enderecos = endereco & 0xFFFFFFFF
        self.barramento_controle["read"] = True
        self.barramento_controle["write"] = False
        self.barramento_controle["tamanho"] = 1

        regiao = self._identificar_regiao(endereco)
        dispositivo = self._dispositivo(regiao)
        local = self._endereco_local(endereco, regiao)

        valor = dispositivo.load_byte(local)
        self.barramento_dados = valor
        return valor

    @validar_acesso(1)
    def store_byte(self, endereco, valor):

        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("Valor precisa ser inteiro")

        if not 0 <= valor <= 0xFF:
            raise ValueError("Valor precisa estar entre 0 e 255")

        self.barramento_enderecos = endereco & 0xFFFFFFFF
        self.barramento_dados = valor
        self.barramento_controle["read"] = False
        self.barramento_controle["write"] = True
        self.barramento_controle["tamanho"] = 1

        regiao = self._identificar_regiao(endereco)
        dispositivo = self._dispositivo(regiao)
        local = self._endereco_local(endereco, regiao)

        dispositivo.store_byte(local, valor)

    @validar_acesso(4)
    def load_word(self, endereco):

        if self._identificar_regiao(endereco) == "IO":
            raise ValueError(
                "Acesso word nao suportado em I/O. Utilize load_byte."
            )

        self.barramento_enderecos = endereco & 0xFFFFFFFF
        self.barramento_controle["read"] = True
        self.barramento_controle["write"] = False
        self.barramento_controle["tamanho"] = 4

        regiao = self._identificar_regiao(endereco)
        if regiao == "RAM":
            valor = self.ram.load_word(self._endereco_local(endereco, regiao))
        else:
            b0 = self.load_byte(endereco)
            b1 = self.load_byte(endereco + 1)
            b2 = self.load_byte(endereco + 2)
            b3 = self.load_byte(endereco + 3)
            valor = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

        self.barramento_dados = valor
        return valor

    @validar_acesso(4)
    def store_word(self, endereco, valor):

        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("Valor precisa ser inteiro")

        if self._identificar_regiao(endereco) == "IO":
            raise ValueError(
                "Acesso word nao suportado em I/O. Utilize store_byte."
            )

        valor &= 0xFFFFFFFF
        self.barramento_enderecos = endereco & 0xFFFFFFFF
        self.barramento_dados = valor
        self.barramento_controle["read"] = False
        self.barramento_controle["write"] = True
        self.barramento_controle["tamanho"] = 4

        regiao = self._identificar_regiao(endereco)
        if regiao == "RAM":
            self.ram.store_word(self._endereco_local(endereco, regiao), valor)
        else:
            self.store_byte(endereco, valor & 0xFF)
            self.store_byte(endereco + 1, (valor >> 8) & 0xFF)
            self.store_byte(endereco + 2, (valor >> 16) & 0xFF)
            self.store_byte(endereco + 3, (valor >> 24) & 0xFF)