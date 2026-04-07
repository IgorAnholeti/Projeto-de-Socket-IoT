import socket
import json
import threading
from protocolo import *

# ==============================
# CONFIGURAÇÃO DO DISPOSITIVO
ID_DISPOSITIVO = "termometro_sala_01"

# ==============================
# CONEXÃO COM SERVIDOR
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP_SERVIDOR, PORTA))

print(f"[CONECTADO] {ID_DISPOSITIVO}")

# ==============================
# ESCUTAR COMANDOS DO SERVIDOR
def ouvir_servidor():
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"\n[MENSAGEM DO SERVIDOR]: {data.strip()}")
        except:
            break

# ==============================
# ENVIO DE REGISTRO
mensagem_registro = json.dumps({
    CAMPO_MSG: MSG_REGISTRO,
    CAMPO_ID: ID_DISPOSITIVO,
    CAMPO_TIPO: TIPO_TERMOMETRO
})

sock.send((mensagem_registro + DELIMITADOR).encode('utf-8'))

# Iniciar thread de escuta
threading.Thread(target=ouvir_servidor, daemon=True).start()

# ==============================
# LOOP DE SIMULAÇÃO MANUAL
while True:
    try:
        print("\n===== TERMÓMETRO (CONTROLO AC) =====")
        print("Digite a temperatura (ex: 28.5)")
        print("'q' - Sair")

        entrada = input("Escolha: ").strip()

        if entrada.lower() == "q":
            break

        # Tentar converter para float para validar a entrada
        temperatura = float(entrada)

        # ==============================
        # ENVIO DE DADOS
        mensagem = json.dumps({
            CAMPO_MSG: MSG_DADOS,
            CAMPO_ID: ID_DISPOSITIVO,
            CAMPO_TIPO: TIPO_TERMOMETRO,
            CAMPO_VALOR: temperatura
        })

        sock.send((mensagem + DELIMITADOR).encode('utf-8'))
        print(f"[TERMÓMETRO] Temperatura de {temperatura}°C enviada.")

    except ValueError:
        print("[ERRO] Por favor, insira um número válido.")
    except Exception as e:
        print(f"[ERRO] {e}")
        break

sock.close()
