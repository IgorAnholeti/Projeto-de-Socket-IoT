import socket
import json
from protocolo import *

# ==============================
# CONFIGURAÇÃO DO DISPOSITIVO
# ==============================

ID_DISPOSITIVO = "sensor_sala_01"

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
    CAMPO_TIPO: TIPO_SENSOR_PRESENCA
})

sock.send((mensagem_registro + DELIMITADOR).encode('utf-8'))

# ==============================
# LOOP DE SIMULAÇÃO
# ==============================

while True:
    try:
        print("\n===== SENSOR DE PRESENÇA =====")
        print("1 - Detectar presença")
        print("0 - Sem presença")
        print("q - Sair")

        entrada = input("Escolha: ").strip()

        if entrada.lower() == "q":
            print("Encerrando sensor...")
            break

        if entrada not in ["0", "1"]:
            print("Valor inválido.")
            continue

        # ==============================
        # ENVIO DE DADOS
        # ==============================

        mensagem = json.dumps({
            CAMPO_MSG: MSG_DADOS,
            CAMPO_ID: ID_DISPOSITIVO,
            CAMPO_TIPO: TIPO_SENSOR_PRESENCA,
            CAMPO_VALOR: entrada
        })

        sock.send((mensagem + DELIMITADOR).encode('utf-8'))

        if entrada == "1":
            print("[SENSOR] Presença detectada enviada ao servidor")
        else:
            print("[SENSOR] Sem presença enviada")

    except Exception as e:
        print(f"[ERRO] {e}")
        break

sock.close()