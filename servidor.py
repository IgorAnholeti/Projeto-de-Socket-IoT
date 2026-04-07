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
     # with lock para o servidor trancar a porta enquanto roda a função e não haver concorrência de processamento.
    sock = None
    with lock:
        sock = dispositivos_conectados[id_destino] # Ele tira uma cópia rápida do contacto (socket) do dispositivo.
    if not sock:
        print(f"[AVISO] Dispositivo {id_dispositivo} offline.")
        return
    try:
        mensagem = json.dumps({
            CAMPO_MSG: MSG_COMANDO,
            CAMPO_COMANDO: comando,
            CAMPO_VALOR: valor
        })

        # O uso do DELIMITADOR aqui é crucial para o cliente não "colar" mensagens
        sock.send((mensagem + DELIMITADOR).encode('utf-8'))
        # Log de envio (IMPORTANTE)
        print(f"[COMANDO] '{comando}' enviado para {id_destino}")

    except (socket.error, BrokenPipeError) as e:
        print(f"[ERRO] Falha de rede ao enviar para {id_destino}: {e}")
        # Limpeza imediata em caso de socket quebrado
        remover_dispositivo(id_destino)

def remover_dispositivo(id_disp):
    """Função auxiliar para garantir que a remoção seja atómica."""
    with lock:
        dispositivos_conectados.pop(id_disp, None)
        lista_tipos.pop(id_disp, None)


# ==============================
# THREAD DE REGRAS DE NEGÓCIO
def monitorar_regras():
    """Thread que monitora eventos temporais."""
    global estado_residencia

    while True:
        # Cálculo de tempo fora do lock para não prender o sistema
        agora = time.time()
        
        # CORREÇÃO: Usar lock para ler variáveis que o sensor altera constantemente
        with lock:
            ultima = estado_residencia["ultima_presenca"]
            presenca = estado_residencia["presenca_detectada"]
            
        tempo_sem_ninguem = agora - ultima

        # Regra: 10 minutos sem presença
        if presenca and tempo_sem_ninguem > 600:
            print("[LOGICA] 10 min sem presença. Desligando lâmpadas...")
            
            with lock:
                estado_residencia["presenca_detectada"] = False
                # Filtra apenas IDs do tipo lampada
                lampadas = [id_d for id_d, tipo in lista_tipos.items() if tipo == TIPO_LAMPADA]

            for id_disp in lampadas:
                enviar_comando(id_disp, CMD_DESLIGAR)

        time.sleep(5) # Verificação a cada 5s é eficiente
        
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
    # Gerenciando as mensagens 
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
                            with lock:
                            estado_residencia["presenca_detectada"] = True
                            estado_residencia["ultima_presenca"] = time.time()
                             # Coleta IDs aqui dentro
                            lampadas = [d_id for d_id, d_tipo in lista_tipos.items() if d_tipo == TIPO_LAMPADA]

                            print(f"[EVENTO] Presença detectada ({id_dispositivo})")
                             # Chamar enviar_comando FORA de qualquer bloco 'with lock'
                            for d_id in lampadas:
                                enviar_comando(d_id, CMD_LIGAR)

                    # TERMÔMETRO
                    elif tipo == TIPO_TERMOMETRO:
                        temp = float(valor)
                        with lock:
                            estado_residencia["temperatura_atual"] = temp
                            ar_condicionados = [d_id for d_id, d_tipo in lista_tipos.items() if d_tipo == TIPO_AR_CONDICIONADO]

                        print(f"[TEMP] {id_dispositivo}: {temp}°C")

                        if temp > 28:
                            print("[LOGICA] Temperatura alta. Ligando ar condicionado...")
                            # 2. Envia os comandos (SEM LOCK)
                            for d_id in ar_condicionados:
                                enviar_comando(d_id, CMD_LIGAR, 22)
                                
                    # TOMADA (Não precisa de lock para gravar ficheiro)
                    elif tipo == TIPO_TOMADA:
                        print(f"[CONSUMO] {id_dispositivo}: {valor}W")
                        salvar_consumo(id_dispositivo, valor)

    except Exception as e:
        print(f"[ERRO] {id_dispositivo or addr} desconectado: {e}")

    finally:
        if id_dispositivo:
            remover_dispositivo(id_dispositivo) # Usa a função que criamos antes
        conn.close()

        print(f"[DESCONECTADO] {id_dispositivo}")
# ==============================
# INICIALIZAÇÃO DO SERVIDOR
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
