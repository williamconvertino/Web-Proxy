import os
import select
import socket
import ssl
import threading

from proxy_cache import ProxyCache

if os.name == 'nt':
    import keyboard

# Debug level - print out everything from lower values PLUS ...
# 0: basic messages (client request, blocked, connection failed)
# 1: more error/exception details
# 2: detailed filtering info
# 3: detailed connection/cache info
DEBUG_LEVEL = 1

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8080
BUFFER_SIZE = 4096 # bytes
TIMEOUT = 0.25 # seconds

CACHE_SIZE = 2 ** 24 # bytes
CACHE_TTL = 60 # seconds

MODE = 'DENYLIST'

class ProxyServer:

    def __init__(self):
        """Set up the proxy server and start the main thread"""
        self.host = PROXY_HOST
        self.port = PROXY_PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cache = ProxyCache(max_size=CACHE_SIZE, ttl=CACHE_TTL)
        self.ssl_context = ssl.create_default_context()

        if (MODE == 'DENYLIST'):
            self.filter_list = self.read_filter_list('denylist.txt')
        elif (MODE == 'ALLOWLIST'):
            self.filter_list = self.read_filter_list('allowlist.txt')
        else:
            self.filter_list = set()

        server_thread = threading.Thread(target=self.start)
        server_thread.start()

        # I couldn't get the server to stop consistently, but this seems to work
        if os.name == 'nt':
            def stop_server():
                keyboard.wait("esc")
                self.server_socket.close()
            print("Press ESC to stop")
            shutdown_thread = threading.Thread(target=stop_server)
            shutdown_thread.start()
        else:
            print("Ctrl+C to stop")

        try:
            server_thread.join()
        except KeyboardInterrupt:
            self.server_socket.close()
            exit(0)
        if os.name == 'nt':
            shutdown_thread.join()


    def start(self):
        """Main thread: accept incoming connections, assign to child threads"""
        print(f"Running on {self.host}:{self.port}")

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
        """Child thread: apply allow/deny list, check cache, send to destination"""
        # Get the data from the request
        request_data = client_socket.recv(BUFFER_SIZE)
        # print(f"Data:\n{request_data.decode('utf-8')}")
        request_verb, request_url = self.get_verb_url(request_data)

        # Get the destination tuple (host, port) and its IP for filtering
        dest = self.get_host(request_data)
        dest_ip = socket.gethostbyname(dest[0])
        self.log(0, f"{'-'*30}\nClient request: {request_verb} {request_url} ({dest_ip}) port {dest[1]}\n{'-'*30}\n")

        # Check if the destination is blocked, close the connection if it is
        if ((MODE == 'DENYLIST' and dest_ip in self.filter_list)
            or (MODE == 'ALLOWLIST' and dest_ip not in self.filter_list)):
            self.log(0, f"Blocked {dest[0]} ({dest_ip})")
            self.http_status(client_socket, "403 Site Blocked")
            client_socket.close()
            return

        if request_verb == 'CONNECT': # HTTPS
            self.https_forward(client_socket, request_data, dest)
        else: # HTTP
            content = self.cache.get(request_url)
            if content is not None:
                self.log(3, f"HTTP: cache hit {request_url}")
                client_socket.sendall(content)
            else:
                self.http_forward(client_socket, request_data, dest)

        client_socket.close()


    def http_forward(self, client_socket, request_data, dest):
        """Handle a plain HTTP request by forwarding it to the destination"""
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        verb, url = self.get_verb_url(request_data)

        try:
            dest_socket.connect(dest)
        except Exception as e:
            self.log(0, f"HTTP: {verb} {url} - could not connect to port {dest[1]}")
            self.log(1, str(e))
            self.http_status(client_socket, "502 Connection Error")
            client_socket.close()
            return

        dest_socket.sendall(request_data)
        full_content = bytearray()

        # Get response and send all chunks of it to client
        first = True
        while True:
            r_ready, _, x_ready = select.select([dest_socket], [], [dest_socket], TIMEOUT)
            if x_ready or not r_ready:
                self.log(3, f"HTTP: done receiving {url}")
                break
            content = dest_socket.recv(BUFFER_SIZE*2)
            if not content:
                self.log(3, f"HTTP: failed to receive {url}")
                break
            if first:
                self.log(3, f"HTTP: receiving from {dest[0]}:{dest[1]}")
                first = False
            full_content.extend(content)
            client_socket.sendall(content)

        self.cache.insert(url, full_content)
        dest_socket.close()
        client_socket.close()


    def https_forward(self, client_socket, request_data, dest):
        """Handle an HTTPS request by relaying it between client and dest"""
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            dest_socket.connect(dest)
        except Exception as e:
            self.log(0, f"HTTPS: could not connect to {dest[0]}:{dest[1]}")
            self.log(1, str(e))
            self.http_status(client_socket, "502 Connection Error")
            client_socket.close()
            return
        self.http_status(client_socket, "200 OK")
        # verb, url = self.get_verb_url(request_data)

        both_sockets = [client_socket, dest_socket]
        first = True
        while True:
            # wait for one or more sockets to be ready for I/O
            r_ready, _, x_ready = select.select(both_sockets, [], both_sockets, TIMEOUT)
            if x_ready or not r_ready:
                dest_socket.close()
                client_socket.close()
                self.log(3, f"HTTPS: done receiving {dest[0]}:{dest[1]}")
                return
            for sock1 in r_ready: # for each one ready to send, forward its data
                sock2 = dest_socket if sock1 is client_socket else client_socket
                content = sock1.recv(BUFFER_SIZE)
                if not content:
                    dest_socket.close()
                    client_socket.close()
                    self.log(3, f"HTTPS: failed to receive {dest[0]}:{dest[1]}")
                    return
                if first and sock1 is dest_socket:
                    self.log(3, f"HTTPS: receiving from {dest[0]}:{dest[1]}")
                    first = False
                sock2.sendall(content)


    def http_status(self, client_socket, status_msg):
        """Send the specified HTTP status (e.g. 200 OK) to the client socket"""
        client_socket.sendall(f"HTTP/1.1 {status_msg}\r\n\r\n".encode())


    def get_verb_url(self, request_data):
        """
        Given a request, find the destination URL (HTTP) or domain (HTTPS) and
        the HTTP verb involved. Return (verb, url).
        HTTPS proxy requests follow the form "CONNECT domain_name", so the full
        URL is not available.
        """
        ret = request_data.split(b' ', maxsplit=2)
        return ret[0].decode(), ret[1].decode()


    def get_host(self, request_data):
        """Given a request to the proxy, return the destination host/port tuple"""
        host_start = request_data.find(b"Host: ") + 6
        host_end = request_data.find(b"\r\n", host_start)
        host = request_data[host_start:host_end].decode("utf-8")
        host_s = host.split(':')
        default_port = 80
        if self.get_verb_url(request_data)[0] == 'CONNECT':
            default_port = 443
        return (host_s[0], (int(host_s[1]) if len(host_s) > 1 else default_port))


    def read_filter_list(self, filename):
        """
        Read through a file containing a list of domain names or IP addresses,
        resolving domain names as needed. Return a set of IPs for allow/denylist.

        Lines beginning with # are treated as comments and not added to the set.
        """
        filter = set()
        with open(filename, 'r') as file:
            for line in file:
                if not line.startswith('#'):
                    filter.update(socket.gethostbyname_ex(line.strip())[2])
        self.log(2, f"Initialized {MODE} with {len(filter)} entries")
        return filter


    def log(self, level, msg):
        """
        Print a message to standard output with specified "debug level" - the
        message is only printed if the global DEBUG_LEVEL is at least as high as
        the level parameter.
        """
        if level <= DEBUG_LEVEL:
            print(msg)


if __name__ == "__main__":
    proxy = ProxyServer()
