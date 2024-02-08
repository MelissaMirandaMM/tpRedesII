import socket
import os
import base64
import time

HOST = 'localhost'
PORTA = 23240
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = (HOST, PORTA)
diretorio = './pasta'

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
        caminho_completo = os.path.join(diretorio, filename)
        with open(caminho_completo, "wb") as arquivo:
            bufferIsString = b''.join(buffer)
            arquivo_decodificado = base64.b64decode(bufferIsString)
            arquivo.write(arquivo_decodificado)
        print("EXITO: CAMINHO DO ARQUIVO", caminho_completo)
    except Exception as e:
        raise Exception("ERRO: ARQUIVO NAO SALVO", str(e))

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
