import os
import pickle
import socket

# Still ...
# Implementar a criação e verificação da senha.

# Configurações
SERVIDOR_PORTA = 12345
TAMANHO_PACOTE = 1024
DIRETORIO_ARQUIVOS = "arquivos_servidor"
SENHA = "123456"
ESTA_AUTENTICADO = False

def autentica(conexao, senha):
    conexao.send(senha.encode())
    response = conexao.recv(TAMANHO_PACOTE).decode()
    if response == 'OK':
        return True
    else:
        return False


# Função para enviar um pacote
def enviar_pacote(conexao, dados):
    pacote_serializado = pickle.dumps(dados)
    conexao.send(pacote_serializado)

# Função para lidar com a solicitação de lista de arquivos
def lidar_com_lista_arquivos(conexao):
    lista_arquivos = os.listdir(DIRETORIO_ARQUIVOS)
    enviar_pacote(conexao, lista_arquivos)

# Função para lidar com a solicitação de download de um arquivo
def lidar_com_download(conexao, nome_arquivo):
    try:
        with open(os.path.join(DIRETORIO_ARQUIVOS, nome_arquivo), 'rb') as f:
            dados_arquivo = f.read()
        conexao.send('OK'.encode())
        enviar_pacote(conexao, dados_arquivo)
    except FileNotFoundError:
        conexao.send('Arquivo não encontrado.'.encode())

# Função principal do servidor
def servidor():
    # Criação do socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', SERVIDOR_PORTA))
        s.listen()

        print(f"Servidor escutando na porta {SERVIDOR_PORTA}...")

        while True:
            conexao, endereco_cliente = s.accept()
            with conexao:
                print(f"Conexão recebida de {endereco_cliente}")

                # Recebe a requisição do cliente
                dados = conexao.recv(TAMANHO_PACOTE).decode()

                # Decide como lidar com a requisição
                if dados == 'LISTA_ARQUIVOS':
                    lidar_com_lista_arquivos(conexao)
                elif dados.startswith('DOWNLOAD'):
                    _, nome_arquivo = dados.split(' ', 1)
                    lidar_com_download(conexao, nome_arquivo)
                else:
                    print("Comando inválido recebido.")

if __name__ == "__main__":
    servidor()

