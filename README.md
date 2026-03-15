# 🖥️ Simulador Von Neumann

> Simulador didático do ciclo **Fetch → Decode → Execute** da Arquitetura Von Neumann,  
> desenvolvido como parte do trabalho prático da disciplina de **Arquitetura e Organização de Computadores — UniFECAF**.

---

## 📁 Arquivos

| Arquivo | Descrição |
|---|---|
| `simulador-von-neumann.html` | Simulador visual e interativo — roda no navegador |
| `simulador_von_neumann.py` | Simulador no terminal — passo a passo didático |

---

## 🌐 Simulador HTML

Interface visual animada com registradores, barramentos e memória em tempo real.

### Como usar

1. Baixe o arquivo `simulador-von-neumann.html`
2. Abra no navegador (Chrome, Firefox, Edge — qualquer um)
3. Nenhuma instalação necessária

### Funcionalidades

- **4 programas de exemplo** prontos para executar
  - Soma simples: `3 + 7`
  - Subtração: `10 − 4`
  - Contador acumulativo
  - Desvio condicional (`JZ`)
- **Modo passo a passo** — botão `▶ PASSO` avança uma fase por vez (ideal para apresentações)
- **Modo automático** — botão `▶▶ EXECUTAR` com velocidade ajustável
- **Registradores animados** — PC, IR, MAR, MDR, ACC acendem por fase
- **Barramentos em tempo real** — Dados, Endereços e Controle com animação de fluxo
- **Log lateral** — mostra cada micro-operação do ciclo FDE
- **Reset** — reinicia o simulador a qualquer momento

### Fases do ciclo (cores)

| Cor | Fase |
|---|---|
| 🔵 Azul | FETCH — busca da instrução na memória |
| 🟡 Amarelo | DECODE — decodificação pela Unidade de Controle |
| 🟢 Verde | EXECUTE — execução pela ALU ou acesso à memória |

---

## 🐍 Simulador Python

Simulador no terminal com saída colorida e explicação detalhada de cada etapa.

### Requisitos

- Python 3.7 ou superior
- Nenhuma biblioteca externa necessária

### Como usar

```bash
# Modo interativo com pausas didáticas (recomendado)
python simulador_von_neumann.py

# Modo turbo — sem pausas entre etapas
python simulador_von_neumann.py --rapido
```

### Programas disponíveis no menu

| # | Programa | Operação |
|---|---|---|
| 1 | Soma simples | `3 + 7 = 10` |
| 2 | Subtração | `10 - 4 = 6` |
| 3 | Multiplicação | `6 × 7 = 42` |
| 4 | Contador acumulativo | `1 + 2 + 3 + 4 + 5 = 15` |
| 5 | Desvio condicional | Demonstra o `JZ` |

### Modos de execução

- **`[A] Auto`** — executa o programa completo com pausas entre cada fase
- **`[P] Passo a passo`** — você pressiona `Enter` para avançar entre Fetch, Decode e Execute

### Exemplo de saída

```
════════════════════════════════════════════════════════════
 CICLO #1   PC=0x0
════════════════════════════════════════════════════════════
  Memória:
    0x00  LOAD 8      # ACC = MEM[8]        ◄►
    0x01  ADD  9      # ACC = ACC + MEM[9]
    ...

╔══════════════════════════════════════════════════════════╗
║              1. FETCH — Busca da Instrução               ║
╚══════════════════════════════════════════════════════════╝
  [1.1] PC → MAR: PC=0x0 copiado para MAR=0x0
  [1.2] MEM[0x00] → MDR: instrução "LOAD 8" lida
  [1.3] MDR → IR: IR="LOAD 8"
  [1.4] PC incrementado: PC=0x1
```

---

## 🧠 Conjunto de instruções

Ambos os simuladores implementam o mesmo conjunto de instruções:

| Instrução | Operação | Exemplo |
|---|---|---|
| `LOAD addr` | `ACC ← MEM[addr]` | `LOAD 8` |
| `STORE addr` | `MEM[addr] ← ACC` | `STORE 10` |
| `ADD addr` | `ACC ← ACC + MEM[addr]` | `ADD 9` |
| `SUB addr` | `ACC ← ACC - MEM[addr]` | `SUB 7` |
| `MUL addr` | `ACC ← ACC × MEM[addr]` | `MUL 6` |
| `OUT addr` | Exibe `MEM[addr]` na saída | `OUT 10` |
| `JZ addr` | Se `ACC = 0`, `PC ← addr` | `JZ 4` |
| `JMP addr` | `PC ← addr` (incondicional) | `JMP 0` |
| `HALT` | Encerra a execução | `HALT` |

---

## 🏛️ Registradores simulados

| Registrador | Nome completo | Função |
|---|---|---|
| `PC` | Program Counter | Aponta para a próxima instrução |
| `IR` | Instruction Register | Guarda a instrução em execução |
| `MAR` | Memory Address Register | Endereço de memória a acessar |
| `MDR` | Memory Data Register | Dado lido ou a escrever na memória |
| `ACC` | Acumulador | Resultado das operações da ALU |
| `R0` | Registrador auxiliar | Operando secundário da ALU |

---

## 📚 Referências

> VON NEUMANN, John. **First Draft of a Report on the EDVAC**. Philadelphia: Moore School of Electrical Engineering, University of Pennsylvania, 30 jun. 1945. Disponível em: https://archive.org/details/20200901-vN_First_Draft_Report_EDVAC_Moore_Sch_1945. Acesso em: 15 mar. 2026.

> STALLINGS, William. **Arquitetura e organização de computadores**. 10. ed. São Paulo: Pearson, 2017.

> TANENBAUM, Andrew S. **Organização estruturada de computadores**. 6. ed. São Paulo: Pearson, 2013.

---

## 📝 Licença

Projeto acadêmico de uso livre para fins educacionais.  
Disciplina: Arquitetura e Organização de Computadores — UniFECAF.
