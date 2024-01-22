from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
import threading
import json
from datetime import datetime


def process_form_data(data):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    data_dict = {
        "username": data['username'][0],
        "message": data['message'][0]
    }
    with open('storage/data.json', 'r+') as file:
        try:
            json_data = json.load(file)
        except json.JSONDecodeError:
            json_data = {}
        json_data[timestamp] = data_dict
        file.seek(0)
        json.dump(json_data, file, indent=2)
        file.truncate()

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data_parse = urllib.parse.unquote_plus(post_data)
        data_dict = {key: value for key, value in urllib.parse.parse_qs(data_parse).items()}
        

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.sendto(json.dumps(data_dict).encode('utf-8'), ('localhost', 5000))

        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(('localhost', 5000))
        while True:
            data, _ = server_socket.recvfrom(1024)
            decoded_data = data.decode('utf-8')
            form_data = json.loads(decoded_data)
            process_form_data(form_data)


if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    socket_thread = threading.Thread(target=run_socket_server)

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()