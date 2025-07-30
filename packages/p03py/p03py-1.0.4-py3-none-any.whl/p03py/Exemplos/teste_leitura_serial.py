
from p03py import P03SerialInterface, verifica_status
import sys

# CONFIGURAÇÕES - CONFIGURATION
PORTA_SERIAL = 'COM4'
BAUDRATE = 4800
BITS = 7
PARIDADE = 'par'
STOPBITS = 1

# SEPARADOR DECIMAL - Decimal Separator
SEPARADOR_DECIMAL = ','     # ',' para Brasil ou '.' para EUA - ',' for Brazil or '.' for USA

#UTILIZA CHECK SUM
UTILIZA_CHK = False


# Instancia a interface - Instantiate the interface
balanca = P03SerialInterface(
    porta=PORTA_SERIAL,
    baudrate=BAUDRATE,
    bits=BITS,
    paridade=PARIDADE,
    stopbits=STOPBITS,
    separador=SEPARADOR_DECIMAL,
    usar_checksum = UTILIZA_CHK
)

# Conecta
try:
    balanca.conectar()
    if balanca.status != 0:
        raise Exception(balanca.mensagem)
except Exception:
    print(f"📴 {balanca.mensagem}")
    sys.exit(1) # Encerra o programa imediatamente

try:
    #          Reading data from the scale ... Press Ctrl+C to stop.
    print("📦 Lendo dados da balança... Pressione Ctrl+C para parar.\n")
    while True:
        valor_raw, chk_ok, dados_formatados = balanca.ler_pacote()
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
            f"[{status['unibal']}] Motion: {status['emmovimento']}  Overcap: {status['overcap']}   Neg: {status['negdata']}\r"
        )
        print(linha.ljust(100), end='')

except KeyboardInterrupt:
    print("\n🛑 Interrompido pelo usuário.")    # Interrupted by user
finally:
    # encerra conexão - Close connection
    balanca.desconectar()
    if balanca.status != 0:
        print(f"📴 {balanca.mensagem}")
