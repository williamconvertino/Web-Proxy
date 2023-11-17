import socket
import threading
import keyboard  # Make sure to install this library

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8080
BUFFER_SIZE = 4096

class ProxyServer:

    def __init__(self):

        self.host = PROXY_HOST
        self.port = PROXY_PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_thread = threading.Thread(target=self.start)
        server_thread.start()

        # I couldnt get the server to stop consistently, but this seems to work
        def stop_server():
            keyboard.wait("esc")
            self.server_socket.close()

        shutdown_thread = threading.Thread(target=stop_server)
        shutdown_thread.start()

        server_thread.join()
        shutdown_thread.join()
        

    def start(self):

        print(f"Running on {self.host}:{self.port}")
        print("Press ESC to stop")

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                proxy_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                proxy_thread.start()
            except Exception as e:
                # This might cause issues later, but this stops it from showing errors every time I stop the server
                break

    def handle_client(self, client_socket):

        # Get the data from the request
        request_data = client_socket.recv(BUFFER_SIZE)
        # print(f"Data:\n{request_data.decode('utf-8')}")

        # Get the destination
        request_host = self.get_host(request_data).split(":")

        request_dest = request_host[0]
        request_port = int(request_host[1]) if len(request_host) > 1 else 80

        # print(f"Destination: {request_dest}")

        print(f"{'-'*30}\nClient request: {request_dest} on port {request_port}\n{'-'*30}\n")

        # Forward request
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            dest_socket.connect((request_dest, request_port))
        except Exception as e:
            print(f"Could not connect to {request_dest}:{request_port}")
            client_socket.close()
            return    
        
        dest_socket.sendall(request_data)

        # Get response and send to client
        try:
            response_data = dest_socket.recv(BUFFER_SIZE)
            # print(f"Received from {request_data}:{request_port} \n{response_data}")
            client_socket.sendall(response_data)
        except Exception as e:
            # print(f"Error receiving response from {request_dest}:{request_port}")
            pass

        dest_socket.close()
        client_socket.close()

    def get_host(self, request_data):
        host_start = request_data.find(b"Host: ") + 6
        host_end = request_data.find(b"\r\n", host_start)
        host = request_data[host_start:host_end].decode("utf-8")
        return host

if __name__ == "__main__":
    proxy = ProxyServer()
