import socket
import threading

class PureServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def handle_client(self, client_socket, client_address):
        """Menangani komunikasi dengan klien"""
        print(f"Client {client_address} connected.")
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"Received message from {client_address}: {message}")
            except Exception as e:
                print(f"Error: {e}")
                break
        client_socket.close()
        self.clients.remove(client_socket)
        print(f"Client {client_address} disconnected.")

    def start(self):
        """Memulai server untuk mendengarkan koneksi klien"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}...")
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.clients.append(client_socket)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()


class PureClient:
    def __init__(self, server_host='127.0.0.1', server_port=5555):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))

    def send_message(self, message):
        """Mengirim pesan ke server"""
        self.client_socket.sendall(message.encode('utf-8'))

    def receive_message(self):
        """Menerima pesan dari server"""
        data = self.client_socket.recv(1024).decode('utf-8')
        print(f"Received from server: {data}")
