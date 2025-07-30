# Verifica o módulo 'serial' (pyserial)
try:
    import serial
except ImportError:
    print("❌ O módulo 'serial' (pyserial) não está instalado.")
    print("👉 Instale com: pip install pyserial")
    exit(1)

import time
import socket

STX = chr(2)
CR = chr(13)

def calcula_chk(dados: bytes) -> str:
    chk = 0
    for b in dados:
        chk += (b & 0x7F)
    chk = (~chk & 0x7F) + 1
    return chr(chk & 0x7F)

def verifica_status(rre: str):
    swa = ord(rre[0])
    pontodec = swa & 0x07
    if pontodec > 2:
        pontodec -= 2
    else:
        pontodec = 0

    swb = ord(rre[1])
    return {
        "pontodec": pontodec,
        "incbal": '5' if (swa & 0x18) == 0x18 else '2' if (swa & 0x10) else '1',
        "netmode": 'S' if (swb & 0x01) > 0 else 'N',
        "negdata": 'S' if (swb & 0x02) > 0 else 'N',
        "overcap": 'S' if (swb & 0x04) > 0 else 'N',
        "emmovimento": 'S' if (swb & 0x08) > 0 else 'N',
        "unibal": 'kg' if (swb & 0x10) > 0 else 'lb'
    }

def acerta_peso(valor_raw, ponto_decimal, separador):
    valor_int = int(valor_raw.lstrip("0") or "0")
    valor_abs_str = str(abs(valor_int)).zfill(ponto_decimal + 1)
    inteiro = valor_abs_str[:-ponto_decimal] if ponto_decimal else valor_abs_str
    decimal = valor_abs_str[-ponto_decimal:] if ponto_decimal else ''
    sinal = '-' if valor_int < 0 else ''
    return f"{sinal}{int(inteiro)}{separador}{decimal}".rstrip(separador)

def preenche_variaveis(rre: str, separador: str = ','):
    status = verifica_status(rre)
    ponto = status['pontodec']
    negdata = status['negdata']

    tara_int = int(rre[9:15])
    liquido_int = int(rre[3:9])
    if negdata == 'S' and liquido_int != 0:
        liquido_int = -abs(liquido_int)

    bruto_int = tara_int + liquido_int

    gross = acerta_peso(str(bruto_int), ponto, separador)
    tare = acerta_peso(str(tara_int), ponto, separador)
    net = acerta_peso(str(liquido_int), ponto, separador)

    return {
        "gross": gross,
        "tare": tare,
        "net": net,
        **status
    }

class MaquinaEstadoBase:
    def __init__(self, separador=',', usar_checksum=True):
        self.estado = 0
        self.buffer = bytearray()
        self.separador = separador
        self.usar_checksum = usar_checksum

    def reset(self):
        self.estado = 0
        self.buffer.clear()

    def processar_byte(self, byte: int):
        if self.estado == 0:
            if byte == 2:
                self.buffer = bytearray([byte])
                self.estado = 1
        elif self.estado == 1:
            self.buffer.append(byte)
            if byte == 13:
                if not self.usar_checksum:
                    return True
                else:
                    self.estado = 2
        elif self.estado == 2:
            self.buffer.append(byte)
            return True
        return False

class P03SerialInterface(MaquinaEstadoBase):
    def __init__(self, porta, baudrate, bits, paridade, stopbits, separador=',', usar_checksum=True):
        super().__init__(separador, usar_checksum)
        self.serial = serial.Serial()
        self.serial.port = porta
        self.serial.baudrate = baudrate
        self.serial.bytesize = bits
        self.serial.parity = {
            'par': serial.PARITY_EVEN,
            'ímpar': serial.PARITY_ODD,
            'nenhum': serial.PARITY_NONE
        }[paridade]
        self.serial.stopbits = stopbits
        self.serial.timeout = 2
        self.mensagem = ""
        self.status = 0

    def conectar(self):
        self.mensagem = ""
        self.status = 0
        if self.usar_checksum:
            self.QtdB = 18
        else:
            self.QtdB = 17
        try:
            self.serial.open()
            self.serial.reset_input_buffer()
        except Exception as e:
            self.mensagem = f"❌ Erro ao abrir porta serial: {e}"
            self.status = 1

    def desconectar(self):
        try:
            self.serial.close()
        except:
            pass
        self.mensagem = "🔌 Conexão serial encerrada"
        self.status = 0

    def ler_pacote(self):
        self.reset()
        self.serial.reset_input_buffer()
        inicio = time.time()
        while time.time() - inicio < 3:  # timeout de 3 segundos
            byte = self.serial.read(1)
            if not byte:
                continue
            if self.processar_byte(byte[0]):
                break
        else:
            # Timeout de 3 segundos sem fechar pacote
            self.status = 1
            self.mensagem = "❌ Timeout: nenhum pacote completo recebido."
            return None, False, None

        # Proteção contra pacotes curtos
        if len(self.buffer) < self.QtdB:
            self.status = 1
            self.mensagem = "❌ Pacote incompleto: dados insuficientes."
            return None, False, None

        if self.usar_checksum:
        	dados_chk = self.buffer[0:-1]
        	chk_recebido = chr(self.buffer[-1])
        	chk_calculado = calcula_chk(dados_chk)

        	ok = chk_recebido == chk_calculado

        	valor = ''.join(map(chr, self.buffer[1:-2]))  #tira CR e chksum
        else:
        	ok = True	#só pra nao dar erro

        	valor = ''.join(map(chr, self.buffer[1:-1]))  #tira CR

        parsed = preenche_variaveis(valor, self.separador) if ok else None
        return valor, ok, parsed

class P03TCPInterface(MaquinaEstadoBase):
    def __init__(self, ip, porta, separador=',',  usar_checksum=True):
        super().__init__(separador, usar_checksum)
        self.ip = ip
        self.porta = porta
        self.socket = None
        self.mensagem = ""
        self.status = 0

    def conectar(self):
        self.mensagem = ""
        self.status = 0
        try:
            self.socket = socket.create_connection((self.ip, self.porta), timeout=5)
            self.socket.settimeout(5)
        except ConnectionRefusedError:
            self.mensagem = "[Erro 10061] Nenhuma conexão pôde ser feita porque a máquina de destino recusou ativamente."
            self.status = 1
        except Exception as e:
            self.mensagem = f"❌ Erro inesperado ao conectar: {e}"
            self.status = 1

    def desconectar(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.mensagem = "🔌 Conexão TCP encerrada"
            self.status = 0

    def ler_pacote(self):
        if not self.socket:
            self.mensagem = "❌ Socket inválido ou desconectado."
            self.status = 1
            return None, False, None
        self.reset()
        try:
            while True:
                try:
                    byte = self.socket.recv(1)
                except (socket.timeout, OSError) as e:
                    self.mensagem = f"⚠️ Erro durante leitura: {e}"
                    self.socket = None
                    self.status = 1
                    return None, False, None

                if not byte:
                    self.mensagem = "⚠️ Conexão perdida. Socket encerrado."
                    self.desconectar()
                    self.socket = None
                    self.status = 1
                    return None, False, None

                if self.processar_byte(byte[0]):
                    break
        except Exception as e:
            self.mensagem = f"🚨 Erro inesperado na leitura: {e}"
            self.socket = None
            self.status = 1
            return None, False, None

        if self.usar_checksum:
        	dados_chk = self.buffer[0:-1]
        	chk_recebido = chr(self.buffer[-1])
        	chk_calculado = calcula_chk(dados_chk)

        	ok = chk_recebido == chk_calculado

        	valor = ''.join(map(chr, self.buffer[1:-2]))  #tira CR e chksum
        else:
        	ok = True	#só pra nao dar erro

        	valor = ''.join(map(chr, self.buffer[1:-1]))  #tira CR

        parsed = preenche_variaveis(valor, self.separador) if ok else None
        return valor, ok, parsed
