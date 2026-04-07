import socket
import json
from protocolo import *

# ==============================
# CONFIGURAÇÃO DO DISPOSITIVO
# ==============================

ID_DISPOSITIVO = "lampada_sala_01"
estado = "desligada"

# ==============================
# CONEXÃO COM SERVIDOR
# ==============================

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP_SERVIDOR, PORTA))

print(f"[CONECTADO] {ID_DISPOSITIVO}")

# ==============================
# ENVIO DE REGISTRO
# ==============================

mensagem_registro = json.dumps({
    CAMPO_MSG: MSG_REGISTRO,
    CAMPO_ID: ID_DISPOSITIVO,
    CAMPO_TIPO: TIPO_LAMPADA
})

sock.send((mensagem_registro + DELIMITADOR).encode('utf-8'))

# ==============================
# LOOP DE RECEBIMENTO
# ==============================

buffer = ""

while True:
    try:
        data = sock.recv(1024).decode('utf-8')

        if not data:
            print("[DESCONECTADO] Servidor encerrou conexão")
            break

        buffer += data

        # Processar mensagens completas
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
                    estado = "ligada"
                    print(f"[LÂMPADA] {ID_DISPOSITIVO} → LIGADA")

                elif comando == CMD_DESLIGAR:
                    estado = "desligada"
                    print(f"[LÂMPADA] {ID_DISPOSITIVO} → DESLIGADA")

    except Exception as e:
        print(f"[ERRO] {e}")
        break

sock.close()