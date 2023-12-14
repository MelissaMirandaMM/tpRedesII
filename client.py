import socket
import pickle

# Still ...
# Adicionar uma etapa para solicitar ou baixar um arquivo específico após receber a lista.

SERVIDOR_ENDERECO = '127.0.0.1'
SERVIDOR_PORTA = 12345
TAMANHO_PACOTE = 1024


def receber_pacote(conexao):
    try:
        pacote_serializado = conexao.recv(TAMANHO_PACOTE)
        return pickle.loads(pacote_serializado)
    except EOFError:
        print("Erro: Não foi possível desserializar o pacote.")
        return None


def solicitar_lista_arquivos(conexao):
    conexao.send('LISTA_ARQUIVOS'.encode())
    return receber_pacote(conexao)


def cliente():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVIDOR_ENDERECO, SERVIDOR_PORTA))
        print("Conectado ao servidor.")

        lista_arquivos = solicitar_lista_arquivos(s)

        if lista_arquivos is not None:
            print("Lista de Arquivos Disponíveis:")
            for arquivo in lista_arquivos:
                print(arquivo)


if __name__ == "__main__":
    cliente()
