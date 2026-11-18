# Roteiro de Apresentação e Demonstração do Projeto
## Simulador de Computador RISC-V (RV32I + Zbb CLZ)
**Disciplina:** Organização de Computadores  
**Docente:** Prof. Walter S. Oliveira  
**Instituição:** Universidade Católica de Santos (UniSantos)  
**Grupo:** Grupo 3 (Instrução Exclusiva: `CLZ` - Count Leading Zeros)

---

## 🎯 Objetivo da Apresentação
Demonstrar o funcionamento integral do simulador de computador RISC-V, comprovando o atendimento de **100% dos requisitos obrigatórios (10 pontos)** e de **três itens de pontuação extra (+5 pontos)**:
1. Memória Cache de 256 linhas com MMU (+2 pontos)
2. Interrupção externa de hardware via teclado (+1 ponto)
3. Interface interativa com edição de registradores e memória (+2 pontos)

---

## ⏱️ Roteiro do Vídeo / Apresentação (Minutagem Sugerida: 6 a 8 minutos)

### [00:00 - 01:15] Introdução e Visão Geral da Arquitetura
- **O que falar:**
  > "Olá professor Walter e colegas. Esta é a apresentação do projeto final de Organização de Computadores da UniSantos. Desenvolvemos um simulador completo de computador baseado na arquitetura aberta RISC-V RV32I em Python, estruturado nos blocos clássicos de von Neumann: Processador de Ciclo Único, Barramento dividido em 3 partes, Memória RAM com mapeamento estrito, Memória de Vídeo VRAM com renderização ASCII no terminal, Periféricos de Hardware MMIO e Memória Cache de 256 linhas. Como pertencemos ao Grupo 3, nossa instrução especial exclusiva é a CLZ (Count Leading Zeros da extensão Zbb)."
- **O que mostrar:**
  - Mostrar os arquivos do projeto no VS Code e a árvore de diretórios (`cpu/`, `memoria/`, `devices/`, `programs/`, `tests/`).

---

### [01:15 - 02:45] Suíte de Testes Automatizados (Qualidade de Código)
- **O que falar:**
  > "Para garantir que cada instrução e componente de hardware funcione com precisão de acordo com a especificação formal do RISC-V, construímos uma suíte de 69 testes unitários utilizando pytest, cobrindo operações lógicas e aritméticas da ULA, decodificação de todos os formatos (R, I, S, B, U, J, SYS), barramento com limites de fronteira, MMIO do terminal, VRAM, Cache e Interrupções."
- **Comando a executar no terminal:**
  ```bash
  pytest -v
  ```
- **O que destacar:**
  - Todos os 69 testes passando em frações de segundo com 100% de sucesso.

---

### [02:45 - 04:30] Demonstração do Programa Unificado (`programs/sistema_completo.hex`)
- **O que falar:**
  > "Agora vamos executar nosso programa de demonstração que integra todas as exigências do edital: ele lê dados da RAM via LW, calcula zeros à esquerda usando nossa instrução CLZ em um laço controlado por BNE, escreve resultados de volta na RAM com SW, transmite texto para o registrador de hardware DATA_OUT do terminal e preenche a VRAM utilizando exclusivamente instruções STORE WORD (SW). Além disso, ativamos a transmissão periódica da VRAM a cada 50 instruções e o dump da memória RAM em matriz de exatamente 32 colunas."
- **Comando a executar no terminal:**
  ```bash
  python main.py programs/sistema_completo.hex --vram --vram-intervalo 50 --dump-ram --ram-inicio 0x200 --ram-linhas 4 --dump-regs
  ```
- **O que destacar na tela:**
  1. **Transmissão Periódica:** As capturas da VRAM sendo impressas automaticamente aos 50 ciclos, 100 ciclos e no final.
  2. **Saída do Terminal:** O texto `[RV32I] SISTEMA COMPLETO OK` recebido do registrador MMIO `0x9FC04`.
  3. **Matriz de 32 Colunas da RAM:** O setor `0x200` com os dados de entrada (`01 00 00 00 02 00 ...`) e o setor `0x240` com os resultados do `CLZ` (`1F 00 00 00 1E 00 00 00 ...` = 31, 30, 29, 28).
  4. **Quadro ASCII da VRAM:** O desenho com moldura `UNISANTOS OC / RV32I + CLZ`.
  5. **Tabela de Registradores:** Todos os 32 registradores (`x0` até `x31`) com seus respectivos nomes da ABI RISC-V (`zero`, `ra`, `sp`, `a0`, etc.).

---

### [04:30 - 05:45] Pontuação Extra: Memória Cache de 256 Linhas com MMU (+2 Pontos)
- **O que falar:**
  > "Como item de pontuação extra, implementamos uma Memória Cache com 256 linhas posicionada entre a CPU e o Barramento, conforme a Figura 6 do edital. Ela possui controlador MMU com política Write-Back, Write-Allocate e suporte tanto a Mapeamento Direto quanto Associativo em Conjunto (2 vias ou 4 vias) com algoritmo de substituição LRU. Regiões de E/S e VRAM possuem bypass automático. Vamos executar o simulador com a cache associativa de 2 vias ativada."
- **Comando a executar no terminal:**
  ```bash
  python main.py programs/sistema_completo.hex --cache --cache-vias 2
  ```
- **O que destacar na tela:**
  - O relatório emitido ao final:
    * Total de acessos
    * Hits de leitura e escrita
    * Misses
    * **Taxa de acerto (Hit Rate) de 88.59%**, comprovando a eficiência da localidade espacial e temporal do algoritmo!

---

### [05:45 - 07:15] Pontuação Extra: Interrupção por Teclado e Interatividade ao Vivo (+3 Pontos)
- **O que falar:**
  > "Para os itens de interrupção externa via teclado (+1 ponto) e interatividade (+2 pontos), vamos abrir o modo interativo passo-a-passo (`--step`). Aqui podemos avançar ciclo a ciclo, disparar interrupções externas de hardware e inclusive alterar registradores ou posições da memória em tempo de execução."
- **Comando a executar no terminal:**
  ```bash
  python main.py programs/sistema_completo.hex --step
  ```
- **Sequência de ações interativas para demonstrar ao vivo:**
  1. Pressionar `Enter` 2 ou 3 vezes: mostra a instrução sendo buscada, decodificada e desmontada em assembly em tempo real.
  2. Digitar `m`: exibe instantaneamente a matriz de 32 colunas da RAM.
  3. Digitar `set r x5 0x123`:
     - O simulador confirma: `[✓] Registrador x5 atualizado para 0x00000123`.
  4. Digitar `r`: mostra que `x5` realmente foi atualizado no banco de registradores!
  5. Digitar `tecla A`:
     - O simulador confirma: `[✓] Tecla 'A' enviada! Interrupção de hardware de teclado gerada.`
     - No próximo passo, a CPU atende a interrupção, desvia para a rotina ISR em `0x00040`, salva o endereço de retorno em `mepc` e retorna via `MRET`.
  6. Digitar `c`: o programa continua até o final e conclui com êxito!

---

### [07:15 - 07:45] Conclusão
- **O que falar:**
  > "O simulador implementa com fidelidade a especificação RV32I e todas as diretrizes do edital da UniSantos, incluindo barramento triplo, E/S programada com VRAM periódica, programa de teste unificado e os bônus de cache, interrupção e interatividade. Agradecemos a atenção do professor Walter."

---

## ❓ Perguntas Frequentes Preparadas para a Arguição do Professor

### 1. "Como a instrução especial CLZ do Grupo 3 foi implementada?"
- **Resposta:**
  A instrução `CLZ` pertence à extensão padrão **Zbb** (Bit Manipulation). Ela foi codificada como uma instrução Tipo-I com `opcode = 0x13`, `funct3 = 0x1` e o imediato de 12 bits fixo em `0x600` (`imm[11:0] = 0b011000000000`), tendo `rs2 = 0`. Na ULA (`cpu/alu.py`), calculamos `32 - valor.bit_length()` com máscara de 32 bits, tratando `0` como `32`.

### 2. "Como o barramento gerencia as interrupções de hardware?"
- **Resposta:**
  O barramento possui três linhas funcionais: `barramento_dados` (32 bits), `barramento_enderecos` (32 bits) e `barramento_controle`. No controle, mantemos os sinais `int_req` (pedido de interrupção) e `int_ack` (confirmação). Quando o teclado/terminal recebe um byte, ele seta `int_req = True`. No fim de cada ciclo de instrução (conforme a Figura 7 do edital), a CPU verifica essa linha se as interrupções estiverem habilitadas, salva o endereço de retorno no registrador `mepc`, chama `atender_interrupcao()` (que emite o `int_ack`) e salta para o vetor pré-definido `0x00040`. O retorno é feito pela instrução `MRET` (`0x30200073`).

### 3. "Por que a VRAM e os registradores de E/S possuem bypass na Memória Cache?"
- **Resposta:**
  Porque VRAM e periféricos MMIO (`0x80000` em diante) são regiões mapeadas em hardware com efeitos colaterais imediatos. Se a escrita na VRAM ou no registrador `DATA_OUT` ficasse retida em uma linha da cache com política write-back, o caractere não apareceria no terminal ou na tela até que houvesse um flush ou substituição de bloco. Portanto, apenas a RAM principal (`0x00000` a `0x7FFFF`) é cacheada.

### 4. "Como a política de substituição LRU foi implementada na Cache?"
- **Resposta:**
  Cada linha da cache possui um contador de tempo lógico (`ultimo_acesso`). Sempre que um bloco é acessado em um conjunto (seja leitura ou escrita), atualizamos esse carimbo com o relógio global de acessos. Quando ocorre um miss e todas as vias do conjunto estão ocupadas, a MMU varre as vias daquele conjunto e elege a linha com o menor carimbo de acesso para substituição, descarregando-a para a RAM caso o `dirty bit` (`sujo`) esteja ativo.
