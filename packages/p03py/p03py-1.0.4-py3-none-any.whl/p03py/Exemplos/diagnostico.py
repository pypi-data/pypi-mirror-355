
from p03py import P03SerialInterface
import sys
import time

PORTAS = [f'COM{i}' for i in range(1, 9)]
BAUDRATES = [9600, 4800]
BITS = 7
PARIDADE = 'par'
STOPBITS = 1
SEPARADOR = ','

print("📌 Esse teste é apenas para alguns parâmetros, certifique-se na sua balança!")
print("📌 This test checks only a few parameters. Please verify with your scale!\n")

def tentar_leitura(porta, baudrate, usar_checksum):
    print(f"🔍 Testando: Porta {porta}, {baudrate} baud, {BITS} bits, paridade {PARIDADE}, {STOPBITS} stop bit, " +
          ("COM checksum..." if usar_checksum else "SEM checksum..."))

    balanca = P03SerialInterface(
        porta=porta,
        baudrate=baudrate,
        bits=BITS,
        paridade=PARIDADE,
        stopbits=STOPBITS,
        separador=SEPARADOR,
        usar_checksum=usar_checksum
    )

    balanca.conectar()
    if balanca.status != 0:
        print(f"⚠️ Falha ao conectar: {balanca.mensagem}\n")
        return False, None, None, None

    inicio = time.time()
    while time.time() - inicio < 5:
        valor, ok, dados = balanca.ler_pacote()
        if valor and ok and dados:
            balanca.desconectar()
            return True, porta, baudrate, usar_checksum
    balanca.desconectar()
    print("⏱️ Nenhum dado válido recebido na porta dentro do tempo limite.\n")
    return False, None, None, None

def diagnosticar():
    for porta in PORTAS:
        for baud in BAUDRATES:
            for chk in [True, False]:
                sucesso, porta_ok, baud_ok, chk_ok = tentar_leitura(porta, baud, chk)
                if sucesso:
                    modo_chk = "COM checksum" if chk_ok else "SEM checksum"
                    print(f"✅ A balança está enviando na porta {porta_ok}, com {baud_ok} baud, {BITS} bits, paridade {PARIDADE}, {STOPBITS} stop bit, {modo_chk}!")
                    sys.exit(0)

    print("❌ Não foi possível determinar a configuração da balança em nenhuma porta COM1 a COM8.")
    sys.exit(1)

if __name__ == "__main__":
    diagnosticar()
