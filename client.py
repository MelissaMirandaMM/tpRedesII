import socket
import base64
from azure.storage.blob import BlobServiceClient

HOST = 'localhost'
PORTA = 2000
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = (HOST, PORTA)

# Configurar a autenticação corretamente usando a chave de acesso ou SAS
service = BlobServiceClient(account_url="https://felipeazure.blob.core.windows.net/tpredes?si=tpredes&sv=2022-11-02&sr=c&sig=0mufXe5IEIM050%2BjNFgpnRW%2BwGNY29A7Tz5WJLVjpcc%3D",
                            credential="si=tpredes&sv=2022-11-02&sr=c&sig=0mufXe5IEIM050%2BjNFgpnRW%2BwGNY29A7Tz5WJLVjpcc%3D")

# Criar novo container ou acessar um existente
container_name = "tpredes"
container_client = service.get_container_client(container_name)

# Importando a função calcular_checksum
def calcular_checksum(data):
    checksum = 0
    for byte in data:
        checksum += byte
    return checksum & 0xFF  # Retorna apenas os 8 bits menos significativos

def enviar_pacote(pacote, destino):
    udp.sendto(pacote, destino)
    while True:
        try:
            data, addr = udp.recvfrom(1024)
            if data == b'ACK':
                break
        except socket.timeout:
            print("Timeout: Pacote perdido, reenviando...")
            udp.sendto(pacote, destino)

def receber_arquivo(filename):
    buffer = []
    base64_decode = ''

    while base64_decode != b'ENCERRADO':
        base64_string, cliente = udp.recvfrom(5 * 1024)
        base64_decode = base64_string
        if base64_decode != b'ENCERRADO':
            checksum = int(base64_decode[0])  # Extrai o checksum do início dos dados
            data = base64_decode[1:]  # Remove o checksum dos dados
            if checksum == calcular_checksum(data):  # Verifica se o checksum é válido
                buffer.append(data)
                print('PACOTE RECEBIDO')
                udp.sendto(b'ACK', cliente)
            else:
                print('Pacote corrompido! Solicitando retransmissão...')
                # Solicitar retransmissão ou descartar o pacote corrompido
                # Aqui, você pode adicionar a lógica para reenviar um NACK
        else:
            print('PACOTE FINALIZADO')
            udp.sendto(b'ACK', cliente)

    print('FIM DA TRANSMISSAO DO ARQUIVO NO CLIENTE')

    try:
        # Selecionar arquivo do container que possui o mesmo nome do arquivo recebido
        arquivo_selecionado = container_client.get_blob_client(filename)

        # Exibir apenas os arquivos do container que possuem o mesmo nome do arquivo recebido
        print("Arquivo selecionado:", arquivo_selecionado.blob_name)

        # Salvar o arquivo selecionado no container com o mesmo nome do arquivo recebido mesmo se o arquivo já existir
        arquivo_selecionado.upload_blob(base64.b64decode(b''.join(buffer)), overwrite=True)

        # Mostrar mensagem de sucesso
        print("EXITO: ARQUIVO ENVIADO PARA O CONTAINER")
    except Exception as e:
        raise Exception("ERRO: ARQUIVO NÃO SALVO NO CONTAINER", str(e))

udp.bind(('', 24250))
udp.settimeout(5)  # Configura um timeout de 5 segundos

print('SOCKET na porta 24250')

# Solicitar a senha ao usuário
password = input('INFORME A SENHA: ')
# Enviar a senha ao servidor para autenticação
udp.sendto(bytes('password|' + password, 'ascii'), dest)  # Correção aqui

# Receber a resposta do servidor
try:
    msg_confirmation, cliente = udp.recvfrom(5 * 1024 * 1024)
    print(cliente, msg_confirmation.decode('ascii'))

    # Verificar se a senha está correta
    if msg_confirmation.decode('ascii') == 'SENHA INCORRETA':
        print('ERRO: SENHA INCORRETA...')
        udp.close()
    else:
        # Se a senha estiver correta, prosseguir com a seleção do arquivo
        try:
            msg_list, cliente = udp.recvfrom(5 * 1024 * 1024)
            print(cliente, msg_list.decode('ascii'))

            arquivo = input('INFORME O ARQUIVO:')
            udp.sendto(bytes('select_file|'+arquivo, 'ascii'), dest)

            msg_arquivo, cliente = udp.recvfrom(5 * 1024 * 1024)
            print(cliente, msg_arquivo.decode('ascii'))

            receber_arquivo(arquivo)

        except Exception as e:
            print('ERRO...', str(e))

except socket.timeout:
    print("Tempo limite excedido. Encerrando a conexão.")
    udp.close()
