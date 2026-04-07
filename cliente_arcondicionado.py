import socket
import json
import threading
from protocolo import *

# ==============================
# CONFIGURAÇÃO DO DISPOSITIVO
ID_DISPOSITIVO = "ar_condicionado_01"
estado = "desligado"
temperatura_setada = 22.0 # Valor padrão

# ==============================
# CONEXÃO COM SERVIDOR
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP_SERVIDOR, PORTA))

print(f"[CONECTADO] {ID_DISPOSITIVO}")

# ==============================
# ENVIO DE REGISTRO
mensagem_registro = json.dumps({
    CAMPO_MSG: MSG_REGISTRO,
    CAMPO_ID: ID_DISPOSITIVO,
    CAMPO_TIPO: TIPO_AR_CONDICIONADO
})

sock.send((mensagem_registro + DELIMITADOR).encode('utf-8'))

# ==============================
# LOOP DE RECEBIMENTO (ESCUTA)
# ==============================
buffer = ""

while True:
    try:
        data = sock.recv(1024).decode('utf-8')

        if not data:
            print("[DESCONECTADO] Servidor encerrou conexão")
            break

        buffer += data

        while DELIMITADOR in buffer:
            mensagem, buffer = buffer.split(DELIMITADOR, 1)
            msg = json.loads(mensagem)

            msg_tipo = msg.get(CAMPO_MSG)
            comando = msg.get(CAMPO_COMANDO)
            valor = msg.get(CAMPO_VALOR)

            # ==============================
            # PROCESSAMENTO DE COMANDOS
            # ==============================
            if msg_tipo == MSG_COMANDO:
                
                if comando == CMD_LIGAR:
                    estado = "ligado"
                    # Se o servidor enviou uma temperatura específica (ex: 22), atualiza
                    if valor is not None:
                        temperatura_setada = valor
                    print(f"\n[AR-CONDICIONADO] {ID_DISPOSITIVO} -> LIGADO")
                    print(f"[STATUS] Definido para: {temperatura_setada}°C")

                elif comando == CMD_DESLIGAR:
                    estado = "desligado"
                    print(f"\n[AR-CONDICIONADO] {ID_DISPOSITIVO} -> DESLIGADO")

    except Exception as e:
        print(f"[ERRO] {e}")
        break

sock.close()
