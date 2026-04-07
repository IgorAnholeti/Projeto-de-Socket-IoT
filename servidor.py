import socket
import threading
import json
import time
from protocolo import *

# ==============================
# ESTRUTURAS GLOBAIS
# ==============================

# { "id_dispositivo": socket }
dispositivos_conectados = {}

# { "id_dispositivo": tipo }
lista_tipos = {}

# Lock para evitar problemas de concorrência entre threads
lock = threading.Lock()

# Estado global da residência
estado_residencia = {
    "presenca_detectada": False,
    "ultima_presenca": time.time(),
    "temperatura_atual": 0.0
}

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def salvar_consumo(id_disp, valor):
    """Armazena o consumo da tomada em arquivo."""
    with open("consumo_energia.txt", "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] ID: {id_disp} | Consumo: {valor}W\n")


def enviar_comando(id_destino, comando, valor=None):
    """Envia comando para um dispositivo específico."""
    with lock:
        if id_destino not in dispositivos_conectados:
            print(f"[AVISO] Dispositivo {id_destino} offline.")
            return

        sock = dispositivos_conectados[id_destino]

    try:
        mensagem = json.dumps({
            CAMPO_MSG: MSG_COMANDO,
            CAMPO_COMANDO: comando,
            CAMPO_VALOR: valor
        })

        # IMPORTANTE: adicionar delimitador
        sock.send((mensagem + DELIMITADOR).encode('utf-8'))
        # Log de envio (IMPORTANTE)
        print(f"[COMANDO] '{comando}' enviado para {id_destino}")

    except Exception as e:
        print(f"[ERRO] Falha ao enviar para {id_destino}: {e}")

        # Remove dispositivo com erro
        with lock:
            if id_destino in dispositivos_conectados:
                del dispositivos_conectados[id_destino]
                del lista_tipos[id_destino]


# ==============================
# THREAD DE REGRAS DE NEGÓCIO
# ==============================

def monitorar_regras():
    """Thread que monitora eventos temporais."""
    global estado_residencia

    while True:
        tempo_sem_ninguem = time.time() - estado_residencia["ultima_presenca"]

        # Regra: 10 minutos sem presença (600s)
        if estado_residencia["presenca_detectada"] and tempo_sem_ninguem > 600:
            print("[LOGICA] 10 min sem presença. Desligando lâmpadas...")

            estado_residencia["presenca_detectada"] = False

            with lock:
             lampadas = [id_disp for id_disp, tipo in lista_tipos.items() if tipo == TIPO_LAMPADA]

            for id_disp in lampadas:
             enviar_comando(id_disp, CMD_DESLIGAR)

        time.sleep(5)
        
# ==============================
# INTERFACE DE USUÁRIO (MENU)
# ==============================

def interface_usuario():
    while True:
        print("\n===== MENU =====")
        print("1 - Listar dispositivos")
        print("2 - Estado da residência")
        print("3 - Ver consumo")
        print("4 - Enviar comando manual")
        print("5 - Sair")

        opcao = input("Escolha: ")

        if opcao == "1":
            with lock:
                print("\n[DISPOSITIVOS CONECTADOS]")
                for id_disp, tipo in lista_tipos.items():
                    print(f"ID: {id_disp} | Tipo: {tipo}")

        elif opcao == "2":
            with lock:
                print("\n[ESTADO DA RESIDÊNCIA]")
                print(f"Presença: {estado_residencia['presenca_detectada']}")
                print(f"Temperatura: {estado_residencia['temperatura_atual']}°C")

        elif opcao == "3":
            print("\n[CONSUMO REGISTRADO]")
            try:
                with open("consumo_energia.txt", "r") as f:
                    print(f.read())
            except FileNotFoundError:
                print("Nenhum consumo registrado ainda.")

        elif opcao == "4":
            id_destino = input("ID do dispositivo: ")
            comando = input("Comando (ligar/desligar): ")
            valor = input("Valor (opcional, ENTER para ignorar): ")

            if valor == "":
                valor = None

            enviar_comando(id_destino, comando, valor)

        elif opcao == "5":
            print("Encerrando servidor...")
            break

        else:
            print("Opção inválida.")     
        
        time.sleep(0.5)   


# ==============================
# THREAD DE CADA CLIENTE
# ==============================

def lidar_com_cliente(conn, addr):
    """Gerencia comunicação com um cliente."""
    print(f"[NOVA CONEXÃO] {addr}")

    buffer = ""
    id_dispositivo = None

    try:
        while True:
            data = conn.recv(1024).decode('utf-8')

            if not data:
                break

            buffer += data

            # Processa mensagens completas
            while DELIMITADOR in buffer:
                mensagem, buffer = buffer.split(DELIMITADOR, 1)

                msg = json.loads(mensagem)

                msg_tipo = msg.get(CAMPO_MSG)
                id_dispositivo = msg.get(CAMPO_ID)
                tipo = msg.get(CAMPO_TIPO)
                valor = msg.get(CAMPO_VALOR)

                # ==============================
                # REGISTRO DO DISPOSITIVO
                # ==============================
                if msg_tipo == MSG_REGISTRO:
                    with lock:
                        dispositivos_conectados[id_dispositivo] = conn
                        lista_tipos[id_dispositivo] = tipo

                    print(f"[REGISTRO] {tipo.upper()} ID:{id_dispositivo}")

                # ==============================
                # PROCESSAMENTO DE DADOS
                # ==============================
                elif msg_tipo == MSG_DADOS:

                    # SENSOR DE PRESENÇA
                    if tipo == TIPO_SENSOR_PRESENCA:
                        if str(valor) == "1":
                            estado_residencia["presenca_detectada"] = True
                            estado_residencia["ultima_presenca"] = time.time()

                            print(f"[EVENTO] Presença detectada ({id_dispositivo})")

                            # Primeiro coleta os IDs (COM LOCK)
                            with lock:
                             lampadas = [d_id for d_id, d_tipo in lista_tipos.items() if d_tipo == TIPO_LAMPADA]
                             # Depois envia (SEM LOCK)
                             for d_id in lampadas:
                              enviar_comando(d_id, CMD_LIGAR)

                    # TERMÔMETRO
                    elif tipo == TIPO_TERMOMETRO:
                        temp = float(valor)
                        estado_residencia["temperatura_atual"] = temp

                        print(f"[TEMP] {id_dispositivo}: {temp}°C")

                        if temp > 28:
                            print("[LOGICA] Temperatura alta. Ligando ACs...")

                           # 1. Coleta os dispositivos (COM LOCK)
                        with lock:
                            ar_condicionados = [
                                d_id for d_id, d_tipo in lista_tipos.items()
                                if d_tipo == TIPO_AR_CONDICIONADO
                        ]

                           # 2. Envia os comandos (SEM LOCK)
                        for d_id in ar_condicionados:
                         enviar_comando(d_id, CMD_LIGAR, 22)

                    # TOMADA
                    elif tipo == TIPO_TOMADA:
                        print(f"[CONSUMO] {id_dispositivo}: {valor}W")
                        salvar_consumo(id_dispositivo, valor)

    except Exception as e:
        print(f"[ERRO] {id_dispositivo} desconectado: {e}")

    finally:
        # Remover cliente
        with lock:
            if id_dispositivo in dispositivos_conectados:
                del dispositivos_conectados[id_dispositivo]
                del lista_tipos[id_dispositivo]

        conn.close()
        print(f"[DESCONECTADO] {id_dispositivo}")


# ==============================
# INICIALIZAÇÃO DO SERVIDOR
# ==============================
# Loop principal
def aceitar_conexoes():
    while True:
        conn, addr = server.accept()

        thread = threading.Thread(
            target=lidar_com_cliente,
            args=(conn, addr),
            daemon=True
        )
        thread.start()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP_SERVIDOR, PORTA))
server.listen()

print(f"[*] Servidor iniciado em {IP_SERVIDOR}:{PORTA}")

# Thread de regras
threading.Thread(target=monitorar_regras, daemon=True).start()
threading.Thread(target=aceitar_conexoes, daemon=True).start()



        
interface_usuario()