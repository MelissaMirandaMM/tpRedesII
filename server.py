import hashlib
import os
import pickle
import socket
import struct

# Configurações
SERVIDOR_PORTA = 12345
TAMANHO_PACOTE = 1024
DIRETORIO_ARQUIVOS = "arquivos_servidor"
SENHA_SERVIDOR = "123456"
WINDOW_SIZE = 5

def autenticar_cliente(conexao, senha):
    try:
        received_hash = conexao.recv(TAMANHO_PACOTE).decode()
        if received_hash == hashlib.sha256(senha.encode()).hexdigest():
            conexao.send('OK'.encode())
            return True
        else:
            conexao.send('NOK'.encode())
            return False
    except Exception as e:
        print(f"Erro durante a autenticação: {e}")
        return False

def enviar_pacote(conexao, dados):
    pacote_serializado = pickle.dumps(dados)
    conexao.send(pacote_serializado)

def lidar_com_lista_arquivos(conexao):
    try:
        lista_arquivos = os.listdir(DIRETORIO_ARQUIVOS)
        enviar_pacote(conexao, lista_arquivos)
    except Exception as e:
        print(f"Erro ao lidar com a lista de arquivos: {e}")

def lidar_com_download(conexao, nome_arquivo):
    try:
        with open(os.path.join(DIRETORIO_ARQUIVOS, nome_arquivo), 'rb') as f:
            dados_arquivo = f.read()
        conexao.send('OK'.encode())
        enviar_pacote(conexao, dados_arquivo)
    except FileNotFoundError:
        conexao.send('Arquivo não encontrado.'.encode())
    except Exception as e:
        print(f"Erro ao lidar com o download do arquivo: {e}")

def criar_diretorio_arquivos():
    try:
        if not os.path.exists(DIRETORIO_ARQUIVOS):
            os.makedirs(DIRETORIO_ARQUIVOS)
    except Exception as e:
        print(f"Erro ao criar o diretório de arquivos: {e}")

def calcular_checksum(data):
    try:
        # Encode the data before hashing
        data_bytes = data.encode()
        return hashlib.md5(data_bytes).hexdigest()
    except Exception as e:
        print(f"Erro ao calcular o checksum: {e}")
        return None

def criar_pacote(seq_num, data):
    try:
        checksum = calcular_checksum(data.encode())
        header = struct.pack('!I32s', seq_num, checksum.encode())
        return header + data.encode()
    except Exception as e:
        print(f"Erro ao criar o pacote: {e}")
        return None

def extrair_pacote(data):
    try:
        header = data[:36]
        seq_num, checksum = struct.unpack('!I32s', header)
        payload = data[36:]
        return seq_num, checksum.decode(), payload.decode()
    except struct.error as e:
        print(f"Erro ao extrair o pacote: {e}")
        return None

def criar_acknowledgment(seq_num):
    try:
        acknowledgment_data = f"ACK for sequence number {seq_num}"
        acknowledgment_packet = criar_pacote(seq_num, acknowledgment_data)
        return acknowledgment_packet
    except Exception as e:
        print(f"Erro ao criar o acknowledgment: {e}")
        return None

def servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', SERVIDOR_PORTA))
        s.listen()

        print(f"Servidor escutando na porta {SERVIDOR_PORTA}...")

        criar_diretorio_arquivos()

        while True:
            conexao, endereco_cliente = s.accept()
            data = conexao.recv(TAMANHO_PACOTE)
            seq_num, checksum, payload = extrair_pacote(data)

            if checksum == calcular_checksum(payload):
                acknowledgment_packet = criar_acknowledgment(seq_num)
                s.sendto(acknowledgment_packet, endereco_cliente)

                with open(f'received_file_{seq_num}.txt', 'a') as file:
                    file.write(payload)
            else:
                print("Erro: Checksum incorreto. Descartando pacote.")

            with conexao:
                print(f"Conexão recebida de {endereco_cliente}")

                if autenticar_cliente(conexao, SENHA_SERVIDOR):
                    dados = conexao.recv(TAMANHO_PACOTE).decode()

                    if dados == 'LISTA_ARQUIVOS':
                        lidar_com_lista_arquivos(conexao)
                    elif dados.startswith('DOWNLOAD'):
                        _, nome_arquivo = dados.split(' ', 1)
                        lidar_com_download(conexao, nome_arquivo)
                    else:
                        print("Comando inválido recebido.")
                else:
                    print("Erro: Senha de cliente incorreta.")

if __name__ == "__main__":
    servidor()
