import socket
import pickle
import hashlib
import os


# Still ...
# Lidar com timeouts e retransmissões
# Adicionar checksum ou verificação de erros

# Configurações
SERVIDOR_PORTA = 12345
TAMANHO_PACOTE = 1024
END_SERVIDOR = '127.0.0.1'

# Função para calcular o hash MD5 de um arquivo


def calcular_hash(arquivo):
    md5 = hashlib.md5()
    with open(arquivo, 'rb') as f:
        while (pedaco := f.read(8192)):
            md5.update(pedaco)
    return md5.hexdigest()

# Função para enviar um pacote e aguardar ACK


def enviar_pacote(pacote, conexao):
    conexao.send(pickle.dumps(pacote))
    ack = conexao.recv(TAMANHO_PACOTE).decode()
    return ack == 'ACK'

# Função para enviar um arquivo usando Stop-and-Wait


def enviar_arquivo(nome_arquivo, conexao):
    # Verifica se o arquivo existe
    if not os.path.exists(nome_arquivo):
        print(f"O arquivo {nome_arquivo} não existe.")
        return False

    # Lê o arquivo e calcula o hash
    with open(nome_arquivo, 'rb') as f:
        dados = f.read()
        hash_md5 = calcular_hash(nome_arquivo)

    # Divide os dados em pacotes
    pacotes = [dados[i:i + TAMANHO_PACOTE]
               for i in range(0, len(dados), TAMANHO_PACOTE)]

    # Envia cada pacote e aguarda ACK
    for i, pacote in enumerate(pacotes):
        pacote_completo = {'numero': i, 'dados': pacote, 'hash': hash_md5}
        sucesso = enviar_pacote(pacote_completo, conexao)

        # Se falhar, retransmitir o pacote
        if not sucesso:
            print(f"Falha ao enviar o pacote {i}. Retransmitindo...")
            i -= 1  # Volta um pacote

    return True

# Função principal para o servidor


def servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((END_SERVIDOR, SERVIDOR_PORTA))
        s.listen()

        print("Aguardando conexão do cliente...")
        conexao, endereco = s.accept()

        with conexao:
            print(f"Conectado por {endereco}")

            # Recebe o nome do arquivo
            nome_arquivo = conexao.recv(TAMANHO_PACOTE).decode()
            print(f"Recebendo arquivo: {nome_arquivo}")

            # Envia o ACK para o nome do arquivo
            conexao.send('ACK'.encode())

            # Recebe o arquivo
            sucesso = enviar_arquivo(nome_arquivo, conexao)

            if sucesso:
                print("Arquivo enviado com sucesso.")
            else:
                print("Falha ao enviar o arquivo.")

# Função principal para o cliente


def cliente():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((END_SERVIDOR, SERVIDOR_PORTA))

        # Envia o nome do arquivo
        nome_arquivo = 'arquivo.txt'
        s.send(nome_arquivo.encode())

        # Aguarda o ACK para o nome do arquivo
        s.recv(TAMANHO_PACOTE)

        # Envia o arquivo
        enviar_arquivo(nome_arquivo, s)


if __name__ == "__main__":
    servidor()
    cliente()
