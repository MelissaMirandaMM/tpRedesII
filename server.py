import socket
import os
import base64
from azure.storage.filedatalake import DataLakeServiceClient

# Configurações de conexão
account_name = 'felipeazure'
file_system_name = 'BlockBlobStorage'
file_system_client = 'str'
file_system_key = '/subscriptions/f541d637-c00b-4160-8405-dc73034d48b4/resourcegroups/NetworkWatcherRG/providers/Microsoft.Storage/storageAccounts/felipeazure'

# Criando o serviço cliente
service_client = DataLakeServiceClient(account_url=f"https://{account_name}.dfs.core.windows.net", credential=file_system_key)

# Criando o sistema de arquivos se não existir
file_system_client = service_client.create_file_system(file_system=file_system_name)


SENHA_CLIENTE = '123456'
HOST = ''
PORTA = 23240
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
origem = (HOST, PORTA)
udp.bind(origem)
diretorio = './pasta'

destino = ('localhost', 24250)

print('SOCKET na porta 23240')

def calcular_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
    return checksum & 0xFF  # Retorna apenas os 8 bits menos significativos

def verifica_senha(sentence): # Função para verificar a senha
    if sentence == SENHA_CLIENTE:
        udp.sendto(bytes('EXITO: SENHA CORRETA!!!', 'ascii'), destino)
        lista_arquivos = listar_arquivos()  # Renomeando a variável para evitar conflito com o nome da função
        arquivos_str = ', '.join(lista_arquivos)
        udp.sendto(bytes(arquivos_str, 'ascii'), destino)
    else:
        udp.sendto(bytes('ERRO: SENHA INCORRETA...', 'ascii'), destino)

def listar_arquivos(): #Função para listar os arquivos da pasta
    arquivos = os.listdir(diretorio)
    lista_arquivos = []
    for arquivo in arquivos:
        if os.path.isfile(os.path.join(diretorio, arquivo)):
            lista_arquivos.append(arquivo)

    return lista_arquivos

def selecionar_arquivo(filename): #Função para selecionar o arquivo
    if filename not in listar_arquivos():
        udp.sendto(bytes('EXITO: ARQUIVO NÃO ENCONTRADO', 'ascii'), destino)
        raise Exception('ERRO: ARQUIVO NÃO ENCONTRADO')

    udp.sendto(bytes('ENVIANDO O ARQUIVO... ' + filename, 'ascii'), destino)
    enviar_arquivo(filename)

def enviar_arquivo(filename):
    try:
        with open(os.path.join(diretorio, filename), "rb") as arquivo:
            conteudo_arquivo = arquivo.read()
            arquivo_codificado = base64.b64encode(conteudo_arquivo)
            arquivo_str = arquivo_codificado.decode("ascii")

            length = len(arquivo_str)
            tam = len(arquivo_str)

            initial = 0
            final = 1023

            while length > 0:
                data = bytes(arquivo_str[initial:final], 'ascii')
                checksum = calcular_checksum(data)  # Calcula o checksum dos dados
                data_com_checksum = bytes([checksum]) + data  # Anexa o checksum aos dados
                udp.sendto(data_com_checksum, destino)
                print('PACOTE ENVIADO')
                while True:
                    try:
                        ack, addr = udp.recvfrom(1024)
                        if ack == b'ACK':
                            break
                    except socket.timeout:
                        print("Timeout: ACK perdido, reenviando...")
                        udp.sendto(data_com_checksum, destino)

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
    except Exception as e:
        udp.sendto(bytes('ERRO: SERVIDOR COM FALHA', 'ascii'), destino)
        print('ERRO', str(e))
        if str(e) != 'DATAGRAMA MAIOR DO QUE O PERMITIDO NA REDE':
            raise Exception(str(e))
