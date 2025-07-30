import time
from p03py import P03TCPInterface, verifica_status

# CONFIGURAÇÃO TCP/IP (loopback) - TCP/IP CONFIGURATION (loopback)
IP_BALANCA = "127.0.0.1"
PORTA_BALANCA = 9991

# SEPARADOR DECIMAL - Decimal Separator
SEPARADOR_DECIMAL = ','   # ',' para Brasil ou '.' para EUA - ',' for Brazil or '.' for USA

#UTILIZA CHECK SUM
UTILIZA_CHK = False

# Instancia a interface TCP - Instantiate the TCP interface
balanca = P03TCPInterface(IP_BALANCA, PORTA_BALANCA, separador=SEPARADOR_DECIMAL, usar_checksum = UTILIZA_CHK)

# Conecta com tentativa automática - Connect with automatic retry
while True:
    balanca.conectar()
    if balanca.status == 0:
        break
    print(f"🛠️ {balanca.mensagem}")
    time.sleep(2)

try:
    #          Reading data from the scale via TCP... Press Ctrl+C to stop.
    print("📦 Lendo dados da balança via TCP... Pressione Ctrl+C para parar.\n")
    while True:
        valor_raw, chk_ok, dados_formatados = balanca.ler_pacote()
        if balanca.status != 0:
            print(f"🛠️ {balanca.mensagem}")
            balanca.desconectar()
            while True:
                time.sleep(2)
                balanca.conectar()
                if balanca.status == 0:
                    #         Reconnected successfully.
                    print("🔁 Reconectado com sucesso.")
                    break
                print(f"🛠️ {balanca.mensagem}")
            continue

        if valor_raw is None:
            continue

        if not chk_ok:
            print("❌ Checksum inválido.\r", end='')
            continue

        status = verifica_status(valor_raw)

        linha = (
            f"Bruto(Gross): {dados_formatados['gross']:>10}   "
            f"Tara(Tare): {dados_formatados['tare']:>10}   "
            f"Líquido(Net): {dados_formatados['net']:>10}   "
            f"[{status['unibal']}] Motion: {status['emmovimento']}  "
            f"Overcap: {status['overcap']}  Neg: {status['negdata']}\r"
        )
        print(linha, end="")

except KeyboardInterrupt:
    print("🛑 Interrompido pelo usuário.")   # Interrupted by user
finally:
    # encerra conexão - Close connection
    balanca.desconectar()
    if balanca.status != 0:
        print(f"📴 {balanca.mensagem}")

