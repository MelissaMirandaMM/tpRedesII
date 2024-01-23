import hashlib
import pickle
import socket
import struct
import time

SERVIDOR_ENDERECO = '127.0.0.1'
SERVIDOR_PORTA = 12345
TAMANHO_PACOTE = 1024
WINDOW_SIZE = 5
SENHA_CLIENTE = "123456"

def autenticar_servidor(conexao, senha):
    hash_senha = hashlib.sha256(senha.encode()).hexdigest()
    conexao.send(hash_senha.encode())
    response = conexao.recv(TAMANHO_PACOTE).decode()
    return response == 'OK'.encode().decode()

def receber_pacote(conexao):
    try:
        pacote_serializado = conexao.recv(TAMANHO_PACOTE)
        return pickle.loads(pacote_serializado)
    except pickle.UnpicklingError as e:
        print(f"Erro: Não foi possível desserializar o pacote. {e}")
        return None

def solicitar_lista_arquivos(conexao):
    try:
        conexao.send('LISTA_ARQUIVOS'.encode())
        return receber_pacote(conexao)
    except Exception as e:
        print(f"Erro durante a solicitação da lista de arquivos. {e}")
        return None

def calcular_checksum(data):
    return hashlib.md5(data.encode()).hexdigest()

def criar_pacote(seq_num, data):
    checksum = calcular_checksum(data.encode())
    header = struct.pack('!I32s', seq_num, checksum.encode())
    return header + data.encode()

def extrair_pacote(data):
    header = data[:36]
    seq_num, checksum = struct.unpack('!I32s', header)
    payload = data[36:]
    return seq_num, checksum.decode(), payload.decode()

def cliente():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Conectando ao servidor...")
        s.connect((SERVIDOR_ENDERECO, SERVIDOR_PORTA))
        print("Autenticando...")
        if autenticar_servidor(s, SENHA_CLIENTE):
            print("Autenticado com sucesso.")
            lista_arquivos = solicitar_lista_arquivos(s)
            if lista_arquivos is not None:
                print("Lista de Arquivos Disponíveis:")
                for arquivo in lista_arquivos:
                    print(arquivo)
            seq_num = 0
            while True:
                # Simulate data transmission
                data = f"Data from client: {seq_num}"
                packet = criar_pacote(seq_num, data)

                # Simulate packet loss (for testing)
                if seq_num % WINDOW_SIZE != 0:
                    s.send(packet)

                # Receive acknowledgment
                s.settimeout(5.0)  # Set a timeout of 5 seconds
                try:
                    acknowledgment = s.recv(TAMANHO_PACOTE)
                    ack_seq_num, _ , _ = extrair_pacote(acknowledgment)

                    if ack_seq_num == seq_num:
                        print(f"Acknowledgment received for sequence number {seq_num}")
                        seq_num += 1
                        time.sleep(1)  # Simulate transmission delay
                    else:
                        print("Erro: Acknowledgment com número de sequência incorreto.")
                except socket.timeout:
                    print("Timeout: Não recebeu dados do servidor.")
                except struct.error:
                    print("Erro: Não foi possível extrair o pacote.")
        else:
            print("Erro: Senha incorreta.")

if __name__ == "__main__":
    cliente()
