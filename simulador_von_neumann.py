"""
╔══════════════════════════════════════════════════════════╗
║       SIMULADOR VON NEUMANN — NeoCore Tech               ║
║       Arquitetura e Organização de Computadores          ║
║       Ciclo Fetch → Decode → Execute (FDE)               ║
╚══════════════════════════════════════════════════════════╝

Instruções suportadas:
  LOAD  <addr>   → ACC = MEM[addr]
  STORE <addr>   → MEM[addr] = ACC
  ADD   <addr>   → ACC = ACC + MEM[addr]
  SUB   <addr>   → ACC = ACC - MEM[addr]
  MUL   <addr>   → ACC = ACC * MEM[addr]
  OUT   <addr>   → imprime MEM[addr]
  JZ    <addr>   → se ACC == 0, PC = addr
  JMP   <addr>   → PC = addr (desvio incondicional)
  HALT           → encerra execução

Uso:
  python simulador_von_neumann.py           # menu interativo
  python simulador_von_neumann.py --rapido  # sem pausas
"""

import time
import sys
import os

# ─── Configuração ───────────────────────────────────────────
DELAY_FASE   = 0.6    # segundos entre fases FDE
DELAY_ETAPA  = 0.3    # segundos entre etapas internas
MODO_RAPIDO  = '--rapido' in sys.argv

if MODO_RAPIDO:
    DELAY_FASE  = 0.05
    DELAY_ETAPA = 0.01

# ─── Cores ANSI ─────────────────────────────────────────────
class C:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    AZUL    = '\033[94m'     # FETCH
    OURO    = '\033[93m'     # DECODE
    VERDE   = '\033[92m'     # EXECUTE / sucesso
    LARANJA = '\033[91m'     # HALT / erro
    CIANO   = '\033[96m'     # registradores
    MAGENTA = '\033[95m'     # barramentos
    BRANCO  = '\033[97m'     # texto destaque
    CINZA   = '\033[90m'     # comentários/dim

def suporta_cores():
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

USE_COLORS = suporta_cores()

def cor(codigo, texto):
    if not USE_COLORS:
        return texto
    return f"{codigo}{texto}{C.RESET}"

def pausa(t=None):
    if t is None:
        t = DELAY_FASE
    time.sleep(t)


# ══════════════════════════════════════════════════════════════
#   CPU — Registradores e Memória
# ══════════════════════════════════════════════════════════════

class CPU:
    def __init__(self):
        self.PC  = 0       # Program Counter
        self.IR  = None    # Instruction Register
        self.MAR = 0       # Memory Address Register
        self.MDR = None    # Memory Data Register
        self.ACC = 0       # Acumulador
        self.R0  = 0       # Registrador auxiliar
        self.memoria = []  # Memória principal (lista de instruções)
        self.halted = False
        self.ciclos = 0
        self.saida  = []   # Saída do dispositivo OUT

    def carregar_programa(self, programa):
        """Carrega lista de tuplas (instrução, comentário) na memória."""
        self.memoria = list(programa)
        self.PC = 0
        self.IR = None
        self.MAR = 0
        self.MDR = None
        self.ACC = 0
        self.R0  = 0
        self.halted = False
        self.ciclos = 0
        self.saida  = []

    def ler_mem(self, addr):
        if 0 <= addr < len(self.memoria):
            val, _ = self.memoria[addr]
            return val
        raise RuntimeError(f"Endereço inválido: {addr}")

    def escrever_mem(self, addr, val):
        if 0 <= addr < len(self.memoria):
            _, comentario = self.memoria[addr]
            self.memoria[addr] = (val, comentario)
        else:
            raise RuntimeError(f"Endereço inválido: {addr}")

    def dump_regs(self):
        return (
            f"  {cor(C.CIANO,'PC')}={cor(C.BRANCO, hex(self.PC))}  "
            f"{cor(C.CIANO,'IR')}={cor(C.BRANCO, str(self.IR) if self.IR else '----')}  "
            f"{cor(C.CIANO,'MAR')}={cor(C.BRANCO, hex(self.MAR))}  "
            f"{cor(C.CIANO,'MDR')}={cor(C.BRANCO, str(self.MDR) if self.MDR is not None else '----')}  "
            f"{cor(C.CIANO,'ACC')}={cor(C.VERDE, str(self.ACC))}  "
            f"{cor(C.CIANO,'R0')}={cor(C.BRANCO, str(self.R0))}"
        )

    def dump_mem(self, destaque=None):
        linhas = []
        for i, (val, cmnt) in enumerate(self.memoria):
            marcador = ''
            if i == destaque and i == self.PC:
                marcador = cor(C.AZUL, '◄►')
            elif i == destaque:
                marcador = cor(C.OURO, ' ◄ ')
            elif i == self.PC:
                marcador = cor(C.AZUL, ' PC')
            else:
                marcador = '   '
            end = cor(C.CINZA, f"0x{i:02X}")
            v   = cor(C.VERDE, str(val))
            c   = cor(C.CINZA, cmnt)
            linhas.append(f"    {end}  {v:<20} {c:30} {marcador}")
        return '\n'.join(linhas)


# ══════════════════════════════════════════════════════════════
#   EXIBIÇÃO
# ══════════════════════════════════════════════════════════════

def linha(char='─', n=60):
    return cor(C.DIM, char * n)

def cabecalho_fase(nome, cor_fase):
    width = 60
    bar = '═' * width
    titulo = f" {nome} "
    pad = (width - len(titulo)) // 2
    return (
        f"\n{cor(cor_fase, '╔' + bar + '╗')}\n"
        f"{cor(cor_fase, '║' + ' ' * pad + titulo + ' ' * (width - pad - len(titulo)) + '║')}\n"
        f"{cor(cor_fase, '╚' + bar + '╝')}"
    )

def exibir_barramentos(dados=None, endereco=None, controle=None):
    d = cor(C.AZUL,   f"Dados:     {dados}")       if dados     else ''
    e = cor(C.LARANJA,f"Endereço:  {endereco}")     if endereco  else ''
    c = cor(C.VERDE,  f"Controle:  {controle}")     if controle  else ''
    partes = [p for p in [d, e, c] if p]
    if partes:
        print(f"  {cor(C.MAGENTA,'[BARR]')} {' | '.join(partes)}")


# ══════════════════════════════════════════════════════════════
#   CICLO FDE
# ══════════════════════════════════════════════════════════════

def fetch(cpu):
    print(cabecalho_fase('1. FETCH — Busca da Instrução', C.AZUL))
    pausa(DELAY_ETAPA)

    # PC → MAR
    cpu.MAR = cpu.PC
    print(f"  {cor(C.AZUL,'[1.1]')} PC → MAR: PC={hex(cpu.PC)} copiado para MAR={hex(cpu.MAR)}")
    exibir_barramentos(endereco=hex(cpu.MAR), controle='MEM-READ')
    pausa(DELAY_ETAPA)

    # MEM[MAR] → MDR
    cpu.MDR = cpu.ler_mem(cpu.MAR)
    print(f"  {cor(C.AZUL,'[1.2]')} MEM[{hex(cpu.MAR)}] → MDR: instrução \"{cpu.MDR}\" lida")
    exibir_barramentos(dados=str(cpu.MDR), endereco=hex(cpu.MAR), controle='MEM-READ')
    pausa(DELAY_ETAPA)

    # MDR → IR, PC++
    cpu.IR = cpu.MDR
    cpu.PC += 1
    print(f"  {cor(C.AZUL,'[1.3]')} MDR → IR: IR=\"{cpu.IR}\"")
    print(f"  {cor(C.AZUL,'[1.4]')} PC incrementado: PC={hex(cpu.PC)}")
    print(f"\n  {cor(C.DIM, 'Estado dos registradores:')}")
    print(cpu.dump_regs())
    pausa(DELAY_FASE)


def decode(cpu):
    print(cabecalho_fase('2. DECODE — Decodificação', C.OURO))
    pausa(DELAY_ETAPA)

    partes = str(cpu.IR).split()
    opcode = partes[0].upper()
    operando = partes[1] if len(partes) > 1 else None

    print(f"  {cor(C.OURO,'[2.1]')} IR = \"{cpu.IR}\"")
    print(f"  {cor(C.OURO,'[2.2]')} Opcode: {cor(C.BRANCO, opcode)}")
    if operando:
        print(f"  {cor(C.OURO,'[2.3]')} Operando: {cor(C.BRANCO, operando)} (endereço de memória)")
    else:
        print(f"  {cor(C.OURO,'[2.3]')} Sem operando")

    print(f"  {cor(C.OURO,'[2.4]')} UC gera sinais de controle para: {cor(C.BRANCO, opcode)}")
    exibir_barramentos(controle=f'DECODE:{opcode}')
    pausa(DELAY_FASE)

    return opcode, int(operando) if operando is not None else None


def execute(cpu, opcode, operando):
    print(cabecalho_fase('3. EXECUTE — Execução', C.VERDE))
    pausa(DELAY_ETAPA)

    if opcode == 'LOAD':
        cpu.MAR = operando
        val = cpu.ler_mem(operando)
        cpu.MDR = val
        cpu.ACC = val
        exibir_barramentos(dados=str(val), endereco=hex(operando), controle='MEM-READ')
        print(f"  {cor(C.VERDE,'[3.1]')} LOAD: MEM[{hex(operando)}] = {val}")
        print(f"  {cor(C.VERDE,'[3.2]')} MEM → MDR → ACC: ACC = {cor(C.BRANCO, str(cpu.ACC))}")

    elif opcode == 'STORE':
        cpu.MAR = operando
        cpu.MDR = cpu.ACC
        cpu.escrever_mem(operando, cpu.ACC)
        exibir_barramentos(dados=str(cpu.ACC), endereco=hex(operando), controle='MEM-WRITE')
        print(f"  {cor(C.VERDE,'[3.1]')} STORE: ACC={cpu.ACC} → MEM[{hex(operando)}]")

    elif opcode == 'ADD':
        val = cpu.ler_mem(operando)
        cpu.R0 = val
        antigo = cpu.ACC
        cpu.ACC = antigo + val
        exibir_barramentos(dados=str(val), endereco=hex(operando), controle='MEM-READ')
        print(f"  {cor(C.VERDE,'[3.1]')} ADD: MEM[{hex(operando)}] = {val}")
        print(f"  {cor(C.VERDE,'[3.2]')} ALU: {antigo} + {val} = {cor(C.BRANCO, str(cpu.ACC))}")

    elif opcode == 'SUB':
        val = cpu.ler_mem(operando)
        cpu.R0 = val
        antigo = cpu.ACC
        cpu.ACC = antigo - val
        exibir_barramentos(dados=str(val), endereco=hex(operando), controle='MEM-READ')
        print(f"  {cor(C.VERDE,'[3.1]')} SUB: MEM[{hex(operando)}] = {val}")
        print(f"  {cor(C.VERDE,'[3.2]')} ALU: {antigo} - {val} = {cor(C.BRANCO, str(cpu.ACC))}")

    elif opcode == 'MUL':
        val = cpu.ler_mem(operando)
        cpu.R0 = val
        antigo = cpu.ACC
        cpu.ACC = antigo * val
        exibir_barramentos(dados=str(val), endereco=hex(operando), controle='MEM-READ')
        print(f"  {cor(C.VERDE,'[3.1]')} MUL: MEM[{hex(operando)}] = {val}")
        print(f"  {cor(C.VERDE,'[3.2]')} ALU: {antigo} × {val} = {cor(C.BRANCO, str(cpu.ACC))}")

    elif opcode == 'OUT':
        val = cpu.ler_mem(operando)
        cpu.saida.append(val)
        exibir_barramentos(dados=str(val), controle='I/O-WRITE')
        print(f"  {cor(C.VERDE,'[3.1]')} OUT: MEM[{hex(operando)}] = {val}")
        print(f"  {cor(C.VERDE+C.BOLD,'>>> SAÍDA: ')}{cor(C.BRANCO, str(val))}")

    elif opcode == 'JZ':
        exibir_barramentos(controle=f'JZ:{hex(operando)}')
        if cpu.ACC == 0:
            cpu.PC = operando
            print(f"  {cor(C.VERDE,'[3.1]')} JZ: ACC=0 → DESVIO! PC ← {hex(operando)}")
        else:
            print(f"  {cor(C.VERDE,'[3.1]')} JZ: ACC={cpu.ACC} ≠ 0 → sem desvio, PC={hex(cpu.PC)}")

    elif opcode == 'JMP':
        cpu.PC = operando
        exibir_barramentos(controle=f'JMP:{hex(operando)}')
        print(f"  {cor(C.VERDE,'[3.1]')} JMP: PC ← {hex(operando)}")

    elif opcode == 'HALT':
        cpu.halted = True
        print(f"  {cor(C.LARANJA,'[3.1]')} HALT: execução encerrada")
        print(f"  {cor(C.LARANJA,'     ')} ACC final = {cor(C.BRANCO, str(cpu.ACC))}")

    else:
        print(f"  {cor(C.LARANJA,'ERRO:')} instrução desconhecida: \"{opcode}\"")
        cpu.halted = True

    print(f"\n  {cor(C.DIM, 'Estado dos registradores:')}")
    print(cpu.dump_regs())
    pausa(DELAY_FASE)


def executar_programa(cpu):
    """Loop principal do ciclo FDE."""
    MAX_CICLOS = 100  # evita loop infinito

    while not cpu.halted and cpu.ciclos < MAX_CICLOS:
        cpu.ciclos += 1
        print(f"\n{linha('═')}")
        print(cor(C.BOLD + C.BRANCO, f" CICLO #{cpu.ciclos}   PC={hex(cpu.PC)}"))
        print(linha('═'))
        print(f"\n{cor(C.DIM,'  Memória (estado atual):')}")
        print(cpu.dump_mem(destaque=cpu.PC))
        print()
        pausa(DELAY_ETAPA)

        try:
            fetch(cpu)
            opcode, operando = decode(cpu)
            execute(cpu, opcode, operando)
        except RuntimeError as e:
            print(cor(C.LARANJA, f"\n  ERRO DE EXECUÇÃO: {e}"))
            cpu.halted = True

    if cpu.ciclos >= MAX_CICLOS:
        print(cor(C.LARANJA, f"\n  AVISO: Limite de {MAX_CICLOS} ciclos atingido!"))

    print(f"\n{linha('═')}")
    print(cor(C.BOLD + C.VERDE, " ═══ PROGRAMA ENCERRADO ═══"))
    print(linha('═'))
    print(f"\n  {cor(C.CIANO,'Ciclos executados:')} {cpu.ciclos}")
    print(f"  {cor(C.CIANO,'ACC final:        ')} {cpu.ACC}")
    if cpu.saida:
        print(f"  {cor(C.CIANO,'Saída (OUT):      ')} {', '.join(str(x) for x in cpu.saida)}")
    print()


# ══════════════════════════════════════════════════════════════
#   PROGRAMAS DE EXEMPLO
# ══════════════════════════════════════════════════════════════

PROGRAMAS = {
    '1': {
        'nome': 'Soma simples: 3 + 7',
        'descricao': 'Carrega 3, soma com 7, armazena e exibe resultado',
        'memoria': [
            ('LOAD 8',   '# ACC = MEM[8]'),
            ('ADD  9',   '# ACC = ACC + MEM[9]'),
            ('STORE 10', '# MEM[10] = ACC'),
            ('OUT  10',  '# Imprime MEM[10]'),
            ('HALT',     '# Fim do programa'),
            ('---',      '# (vazio)'),
            ('---',      '# (vazio)'),
            ('---',      '# (vazio)'),
            (3,          '# dado: 3'),
            (7,          '# dado: 7'),
            (0,          '# resultado'),
        ]
    },
    '2': {
        'nome': 'Subtração: 10 - 4',
        'descricao': 'Subtrai dois valores da memória',
        'memoria': [
            ('LOAD 6',  '# ACC = MEM[6]'),
            ('SUB  7',  '# ACC = ACC - MEM[7]'),
            ('STORE 8', '# MEM[8] = ACC'),
            ('OUT  8',  '# Imprime resultado'),
            ('HALT',    '# Fim'),
            ('---',     '# (vazio)'),
            (10,        '# dado: 10'),
            (4,         '# dado: 4'),
            (0,         '# resultado'),
        ]
    },
    '3': {
        'nome': 'Multiplicação: 6 × 7',
        'descricao': 'Usa MUL para calcular 6 × 7',
        'memoria': [
            ('LOAD 5',  '# ACC = MEM[5]'),
            ('MUL  6',  '# ACC = ACC * MEM[6]'),
            ('STORE 7', '# MEM[7] = ACC'),
            ('OUT  7',  '# Imprime resultado'),
            ('HALT',    '# Fim'),
            (6,         '# dado: 6'),
            (7,         '# dado: 7'),
            (0,         '# resultado'),
        ]
    },
    '4': {
        'nome': 'Contador acumulativo (1+2+3+4+5)',
        'descricao': 'Loop que soma valores de 1 a 5',
        'memoria': [
            ('LOAD 9',   '# ACC = 0 (acum)'),
            ('ADD  10',  '# ACC += MEM[10] (i)'),
            ('STORE 9',  '# MEM[9] = ACC'),
            ('OUT  9',   '# Exibe acumulado'),
            ('LOAD 10',  '# ACC = i'),
            ('ADD  11',  '# ACC = i + 1'),
            ('STORE 10', '# i = i + 1'),
            ('SUB  12',  '# ACC = i - 6'),
            ('JZ   8',   '# Se i==6, encerra'),
            (0,          '# acumulador'),
            (1,          '# i (início em 1)'),
            (1,          '# incremento'),
            (6,          '# limite (6 - i = 0)'),
            ('HALT',     '# Fim do loop'),
        ]
    },
    '5': {
        'nome': 'Desvio condicional JZ',
        'descricao': 'Demonstra salto condicional quando ACC = 0',
        'memoria': [
            ('LOAD 5',  '# ACC = MEM[5]'),
            ('SUB  6',  '# ACC = ACC - MEM[6]'),
            ('JZ   4',  '# Se ACC=0, vai p/ HALT'),
            ('OUT  7',  '# (só executa se ACC≠0)'),
            ('HALT',    '# Fim'),
            (5,         '# valor: 5'),
            (5,         '# comparar com: 5'),
            (99,        '# valor de saída alternativo'),
        ]
    },
}


# ══════════════════════════════════════════════════════════════
#   MAIN — Menu interativo
# ══════════════════════════════════════════════════════════════

def menu():
    print(cor(C.AZUL + C.BOLD, """
╔══════════════════════════════════════════════════════════╗
║       SIMULADOR VON NEUMANN — NeoCore Tech               ║
║       Arquitetura e Organização de Computadores          ║
╚══════════════════════════════════════════════════════════╝
"""))
    print(cor(C.CIANO, "  Programas disponíveis:"))
    for k, p in PROGRAMAS.items():
        print(f"    {cor(C.OURO, k)}. {p['nome']}")
        print(f"       {cor(C.CINZA, p['descricao'])}")
    print(f"\n    {cor(C.OURO,'6')}. Sair")
    print()

def main():
    cpu = CPU()

    while True:
        menu()
        escolha = input(cor(C.BRANCO, "  → Escolha um programa (1-6): ")).strip()

        if escolha == '6':
            print(cor(C.VERDE, "\n  Simulador encerrado. Bons estudos!\n"))
            break

        if escolha not in PROGRAMAS:
            print(cor(C.LARANJA, "  Opção inválida. Tente novamente.\n"))
            continue

        prog = PROGRAMAS[escolha]
        print(f"\n{cor(C.BOLD + C.AZUL, '  Carregando: ')}{cor(C.BRANCO, prog['nome'])}")
        print(cor(C.CINZA, f"  {prog['descricao']}"))
        print()

        cpu.carregar_programa(prog['memoria'])

        modo = input(cor(C.BRANCO, "  Modo: [A]uto (roda tudo) / [P]asso a passo? ")).strip().upper()

        if modo == 'P':
            # Passo a passo manual
            global DELAY_FASE, DELAY_ETAPA
            orig_fase, orig_etapa = DELAY_FASE, DELAY_ETAPA
            DELAY_FASE = 0
            DELAY_ETAPA = 0

            while not cpu.halted:
                cpu.ciclos += 1
                print(f"\n{linha('═')}")
                print(cor(C.BOLD + C.BRANCO, f" CICLO #{cpu.ciclos}   PC={hex(cpu.PC)}"))
                print(linha('═'))
                print(f"\n{cor(C.DIM,'  Memória:')}")
                print(cpu.dump_mem(destaque=cpu.PC))
                print()
                input(cor(C.DIM, "  [ENTER para FETCH] "))
                fetch(cpu)
                input(cor(C.DIM, "  [ENTER para DECODE] "))
                opcode, operando = decode(cpu)
                input(cor(C.DIM, "  [ENTER para EXECUTE] "))
                execute(cpu, opcode, operando)

            DELAY_FASE, DELAY_ETAPA = orig_fase, orig_etapa

            print(f"\n{linha('═')}")
            print(cor(C.BOLD + C.VERDE, " ═══ PROGRAMA ENCERRADO ═══"))
            print(f"  {cor(C.CIANO,'Ciclos:')} {cpu.ciclos}  |  {cor(C.CIANO,'ACC:')} {cpu.ACC}")
            if cpu.saida:
                print(f"  {cor(C.CIANO,'Saída:')} {', '.join(str(x) for x in cpu.saida)}")
            print()
        else:
            executar_programa(cpu)

        input(cor(C.DIM, "  [ENTER para voltar ao menu] "))
        print('\n' * 2)


if __name__ == '__main__':
    main()
