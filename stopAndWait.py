import socket
import pickle
import hashlib
import os

class Server:
    def __init__(self, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('localhost', port))

    def start(self):
        while True:
            data, client_address = self.server_socket.recvfrom(1024)
            packet = pickle.loads(data)
            if self.validate_checksum(packet):
                self.process_packet(packet)

    def validate_checksum(self, packet):
        checksum = packet['checksum']
        del packet['checksum']  # Remove o checksum para recalculá-lo
        serialized_packet = pickle.dumps(packet)
        new_checksum = hashlib.md5(serialized_packet).hexdigest()
        return checksum == new_checksum

    def process_packet(self, packet):
        if packet['type'] == 'data':
            print(f"Received Data: {packet['data']}")
            self.send_ack(packet['seq'], packet['client_address'])

    def send_ack(self, seq, client_address):
        ack_packet = {'type': 'ack', 'seq': seq}
        serialized_ack = pickle.dumps(ack_packet)
        self.server_socket.sendto(serialized_ack, client_address)


class Client:
    def __init__(self, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = ('localhost', port)
        self.seq = 0

    def send_data(self, data):
        data_packet = {'type': 'data', 'seq': self.seq, 'data': data, 'checksum': ''}
        serialized_data = pickle.dumps(data_packet)
        data_packet['checksum'] = hashlib.md5(serialized_data).hexdigest()  # Calcula o checksum
        serialized_data = pickle.dumps(data_packet)
        self.client_socket.sendto(serialized_data, self.server_address)
        self.receive_ack()

    def receive_ack(self):
        ack, _ = self.client_socket.recvfrom(1024)
        ack_packet = pickle.loads(ack)
        if ack_packet['type'] == 'ack' and ack_packet['seq'] == self.seq:
            print("ACK Received!")
            self.seq += 1


# Exemplo de Uso
if __name__ == "__main__":
    server = Server(12345)
    client = Client(12345)

    # Simula o envio de dados
    for i in range(5):
        client.send_data(f"Data {i}")

    server.start()
