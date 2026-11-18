# Simulador de Processador RISC-V em Python

Simulador de CPU de 32 bits baseado na arquitetura **RISC-V (RV32I)** com suporte à extensão **Zbb (instrução CLZ)**, barramento unificado com mapeamento de memória, periféricos de entrada/saída (Terminal I/O) e framebuffer de vídeo (VRAM) com renderização ASCII no próprio terminal.

---

## Arquitetura do Sistema

O projeto é modularizado nos seguintes componentes:

```
Processador_Python/
├── cpu/
│   ├── alu.py           # Unidade Lógica e Aritmética (ALU) e funções de contagem de zeros (CLZ)
│   ├── decoder.py       # Decodificador de instruções (R, I, S, B, U, J, SYS)
│   ├── processor.py     # Ciclo de busca, decodificação e execução da CPU
│   └── registrador.py   # Banco de registradores (x0..x31 com x0 imutável)
├── memoria/
│   ├── bus.py           # Barramento de comunicação dividido em dados, endereços e controle
│   ├── cache.py         # Memória Cache de 256 linhas com MMU, LRU e Write-Back (Bônus +2 pts)
│   ├── map_memoria.py   # Constantes de mapeamento de memória e limites
│   └── ram.py           # Memória RAM com formatação em matriz de 32 colunas
├── devices/
│   ├── io.py            # Registradores mapeados em memória (DATA_IN, DATA_OUT, STATUS) e interrupções
│   ├── terminal.py      # Terminal para envio e recebimento de caracteres via I/O
│   ├── vram.py          # Memória de vídeo (VRAM)
│   └── vram_viewer.py   # Renderizador ASCII do framebuffer da VRAM para o terminal
├── programs/
│   ├── loader.py        # Carregador de programas em formato hexadecimal (.hex)
│   ├── clz_test.hex     # Programa de teste para instruções CLZ e operações aritméticas
│   ├── system_test.hex  # Programa de demonstração (Terminal I/O + VRAM)
│   └── sistema_completo.hex # Demonstração unificada completa (LW, SW, CLZ, Loops, MMIO e VRAM)
├── tests/               # Suíte completa de 69 testes unitários com pytest
└── main.py              # Interface de Linha de Comando (CLI) para execução e depuração
```

---

## Mapa de Memória (Memory Map)

O barramento (`Bus`) divide o espaço de endereçamento de 32 bits nas seguintes regiões:

| Região | Endereço Inicial | Endereço Final | Tamanho | Descrição |
|---|---|---|---|---|
| **RAM** | `0x00000` | `0x7FFFF` | 512 KiB | Código do programa, dados e pilha |
| **VRAM** | `0x80000` | `0x8FFFF` | 64 KiB | Framebuffer gráfico / texto em modo matriz |
| **Reservado** | `0x90000` | `0x9FBFF` | ~63 KiB | Região protegida (acessos geram exceção) |
| **I/O** | `0x9FC00` | `0x9FFFF` | 1 KiB | Periféricos mapeados em memória (MMIO) |

### Registradores de I/O (MMIO):
- `0x9FC00` (`DATA_IN`): Leitura do próximo caractere da fila de entrada.
- `0x9FC04` (`DATA_OUT`): Escrita de caractere para exibição no terminal.
- `0x9FC08` (`STATUS`): `1` se houver entrada disponível para leitura, `0` caso contrário.

---

## Conjunto de Instruções Suportado

- **Tipo R**: `ADD`, `SUB`, `SLL`, `SLT`, `SLTU`, `XOR`, `SRL`, `SRA`, `OR`, `AND`
- **Tipo I (Aritmético/Lógico)**: `ADDI`, `SLTI`, `SLTIU`, `XORI`, `ORI`, `ANDI`, `SLLI`, `SRLI`, `SRAI`
- **Extensão Zbb**: `CLZ` (Count Leading Zeros - contagem de zeros à esquerda)
- **Tipo I (Carga de Memória)**: `LB`, `LBU`, `LW`
- **Tipo I (Saltos Indiretos)**: `JALR`
- **Tipo S (Escrita em Memória)**: `SB`, `SW`
- **Tipo B (Desvios Condicionais)**: `BEQ`, `BNE`, `BLT`, `BGE`, `BLTU`, `BGEU`
- **Tipo U (Constantes Superiores)**: `LUI`, `AUIPC`
- **Tipo J (Saltos Incondicionais)**: `JAL`
- **Tipo SYS**: `EBREAK`, `ECALL`

---

## Instalação e Requisitos

- Python 3.10 ou superior
- [pytest](https://pytest.org/) para execução dos testes

### Criando e ativando o ambiente virtual (PowerShell)

No diretório raiz do projeto, crie um ambiente virtual:

```powershell
python -m venv .venv
```

Ative-o no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a execução do script de ativação, permita scripts **somente para a sessão atual** e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Com o ambiente ativado, instale as dependências:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para sair do ambiente virtual ao terminar:

```powershell
deactivate
```

> O uso de `-Scope Process` não altera permanentemente a política de execução do Windows: ele vale apenas para a janela atual do PowerShell.


- [pytest](https://pytest.org/) para execução dos testes

Instale as dependências:
```bash
pip install -r requirements.txt
```

---

## 🧪 Executando os Testes

Execute a suíte completa de testes automatizados:
```bash
pytest
```

Para executar testes com saída detalhada:
```bash
pytest -v
```

---

## Utilizando a Interface de Linha de Comando (CLI)

O arquivo `main.py` permite carregar e executar qualquer programa `.hex`:

### 1. Execução Padrão
Executa o programa e apresenta o resumo ao final:
```bash
python main.py programs/clz_test.hex
```

### 2. Exibindo os Registradores ao Final (`--dump-regs`)
Mostra a tabela formatada com todos os registradores (`x0` a `x31`) com seus respectivos nomes da ABI RISC-V:
```bash
python main.py programs/clz_test.hex --dump-regs
```

### 3. Exibição Periódica da VRAM em ASCII (`--vram-intervalo N`)
Transmite o estado da VRAM para o terminal automaticamente a cada $n$ instruções executadas:
```bash
python main.py programs/sistema_completo.hex --vram --vram-intervalo 50
```

### 4. Matriz da Memória RAM em 32 Colunas (`--dump-ram`)
Exibe os setores da memória organizados em exatamente 32 colunas por linha:
```bash
python main.py programs/sistema_completo.hex --dump-ram --ram-inicio 0x200 --ram-linhas 4
```

### 5. Modo Depuração (`-d` ou `--debug`)
Imprime o desmonte de cada instrução executada no ciclo em tempo real:
```bash
python main.py programs/clz_test.hex --debug
```

### 6. Modo Passo-a-Passo Interativo com Edição ao Vivo (`-s` ou `--step`)
Permite avançar instrução por instrução, inspecionando e **alterando registradores e memória em tempo real** (Bônus de Interatividade +2 pontos):
```bash
python main.py programs/sistema_completo.hex --step
```
Comandos disponíveis no prompt interativo:
- `Enter` ou `s`: Avança 1 ciclo de instrução
- `c`: Continua a execução normalmente até o final
- `r`: Exibe a tabela completa de registradores
- `m`: Exibe a matriz de 32 colunas da memória RAM
- `v`: Exibe o estado atual da VRAM em arte ASCII
- `int`: Dispara uma interrupção externa de teste no barramento
- `tecla <char>`: Injeta caractere via teclado e dispara interrupção de hardware
- `set r <reg> <val>`: Altera um registrador na hora (ex: `set r x1 42` ou `set r 5 0x100`)
- `set m <end> <val>`: Altera uma palavra na RAM na hora (ex: `set m 0x200 0xAABBCCDD`)
- `load <hex> [end]`: Grava instrução no PC atual ou endereço especificado
- `goto <end>`: Modifica o PC para outro endereço
- `help` ou `?`: Exibe o menu com todos os comandos interativos
- `q`: Encerra a simulação imediatamente

### 7. Memória Cache de 256 Linhas (`--cache` e `--cache-vias`) 
Ativa a memória cache com 256 linhas posicionada entre a CPU e o Barramento, exibindo ao final o relatório com **Hits, Misses e Hit Rate**:
```bash
python main.py programs/sistema_completo.hex --cache --cache-vias 2
```


### 8. Parâmetros da CLI
```text
usage: main.py [-h] [--pc PC] [--max-ciclos MAX_CICLOS] [-s] [-d] [--dump-regs]
               [--vram] [--vram-intervalo VRAM_INTERVALO] [--vram-largura VRAM_LARGURA]
               [--vram-altura VRAM_ALTURA] [--vram-modo {auto,char,pixel}]
               [--dump-ram] [--ram-inicio RAM_INICIO] [--ram-linhas RAM_LINHAS]
               [--ram-omitir-vazias] [--cache] [--cache-vias {1,2,4}] [-i ENTRADA]
               arquivo
```
