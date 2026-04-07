# CONFIGURAÇÃO DE REDE
IP_SERVIDOR = '127.0.0.1'
PORTA = 5000

# Delimitador de mensagens (IMPORTANTE para TCP)
DELIMITADOR = "\n"

# TIPOS DE DISPOSITIVOS
TIPO_LAMPADA = "lampada"
TIPO_TOMADA = "tomada"
TIPO_SENSOR_PRESENCA = "sensor_presenca"
TIPO_AR_CONDICIONADO = "ar_condicionado"
TIPO_TERMOMETRO = "termometro"


# TIPOS DE MENSAGEM — essencial para registro inicial do cliente/envio de dados/comando do servidor/reposta status
#===== Sem isso o servidor vai ter que adivinhar o que cada transmissão significa.
MSG_REGISTRO = "registro"   # quando cliente conecta
MSG_DADOS = "dados"         # envio de leitura
MSG_COMANDO = "comando"     # servidor -> cliente
MSG_RESPOSTA = "resposta"   # opcional (ack/status)


# COMANDOS / AÇÕES
CMD_LIGAR = "ligar"
CMD_DESLIGAR = "desligar"
CMD_SET_TEMP = "set_temp"

# CAMPOS PADRÃO (opcional, mas recomendado)
CAMPO_ID = "id"
CAMPO_TIPO = "tipo"
CAMPO_MSG = "msg_tipo"
CAMPO_COMANDO = "comando"
CAMPO_VALOR = "valor"