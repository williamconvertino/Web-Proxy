import socket
import threading
import signal
import sys

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8080

class ProxyServer:

    def __init__(self):
        self.start()

    def handle_client(client_socket):
        
        pass

    def start(self):

        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.bind((PROXY_HOST, PROXY_PORT))
        proxy_socket.listen(5)
        self.proxy_socket = proxy_socket

        print(f"Listening on {PROXY_HOST}:{PROXY_PORT}")

        while True:
            print("Running...")

            

        
if __name__ == "__main__":
    ProxyServer()
