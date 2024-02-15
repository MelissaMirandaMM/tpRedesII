import socket
import base64
from azure.storage.blob import BlobServiceClient

# Configurações do servidor UDP
SENHA_CLIENTE = '123456'
HOST = ''
PORTA = 23240
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
origem = (HOST, PORTA)
udp.bind(origem)
udp.settimeout(10)  # Configura um timeout de 10 segundos

destino = ('localhost', 24250)

print('SOCKET na porta 23240')

service = BlobServiceClient(account_url="https://felipeazure.blob.core.windows.net/")

# Criar novo container ou acessar um existente
container_name = "tpredes"
container_client = service.get_container_client(container_name)

def calcular_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
    return checksum & 0xFF  # Retorna apenas os 8 bits menos significativos

# Função para listar os arquivos
def listar_arquivos():
    lista_arquivos = []
    for blob in container_client.list_blobs():
        lista_arquivos.append(blob.name)
    return lista_arquivos

# Função para verificar a senha
def verifica_senha(sentence):
    if sentence == SENHA_CLIENTE:
        udp.sendto(bytes('EXITO: SENHA CORRETA!!!', 'ascii'), destino)
        lista_arquivos = listar_arquivos()
        arquivos_str = ', '.join(lista_arquivos)
        udp.sendto(bytes(arquivos_str, 'ascii'), destino)
    else:
        udp.sendto(bytes('ERRO: SENHA INCORRETA...', 'ascii'), destino)

# Função para selecionar o arquivo
def selecionar_arquivo(filename):
    if filename not in listar_arquivos():
        udp.sendto(bytes('EXITO: ARQUIVO NÃO ENCONTRADO', 'ascii'), destino)
        raise Exception('ERRO: ARQUIVO NÃO ENCONTRADO')

    udp.sendto(bytes('ENVIANDO O ARQUIVO... ' + filename, 'ascii'), destino)
    enviar_arquivo(filename)

# Função para enviar o arquivo via UDP
def enviar_arquivo(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        file_contents = blob_client.download_blob().readall()
        file_contents_base64 = base64.b64encode(file_contents)
        file_contents_str = file_contents_base64.decode("ascii")

        length = len(file_contents_str)
        tam = len(file_contents_str)

        initial = 0
        final = 1023

        while length > 0:
            data = bytes(file_contents_str[initial:final], 'ascii')
            udp.sendto(data, destino)  # Envia os dados via UDP

            initial = final
            if length < 1024:
                final = final + length
            else:
                final = final + 1024
            if length <= 1024:
                length = length - length
            else:
                length = length - 1024

        print('Tamanho do arquivo:', tam)
        print('FIM DA TRANSMISSÃO NO SERVIDOR')
        udp.sendto(b'ENCERRADO', destino)

    except Exception as e:
        print(str(e))
        raise Exception(f"ERRO: FALHA AO ENVIAR ARQUIVO {filename}.")

while True:
    try:
        udp.settimeout(10)  # Defina o timeout dentro do loop para garantir que esteja sempre em vigor
        message, cliente = udp.recvfrom(1024)
        sentence = message.decode('ascii')
        print(cliente, sentence)

        parts = sentence.split("|")
        if len(parts) < 2:
            if sentence == "ACK":
                continue  # Ignora mensagens "ACK"
            else:
                raise Exception("Mensagem mal formatada: {}".format(sentence))

        idetify = parts[0]
        message = parts[1]

        if idetify == "password":
            verifica_senha(message)
        elif idetify == 'select_file':
            selecionar_arquivo(message)

    except socket.timeout:
        print("Tempo esgotado ao aguardar dados do cliente.")
        continue  # Volte para o início do loop para continuar aguardando conexões

    except Exception as e:
        udp.sendto(bytes('ERRO: SERVIDOR COM FALHA', 'ascii'), destino)
        print('ERRO', str(e))
        if str(e) != 'DATAGRAMA MAIOR DO QUE O PERMITIDO NA REDE':
            raise Exception(str(e))