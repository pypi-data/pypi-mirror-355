from __future__ import annotations
import uuid
import msgpack
import requests
import socket
import webbrowser
from IPython.display import IFrame, display

LOCALHOST = 'localhost'
server_port = 5656


def get_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((LOCALHOST, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def start_server():
    from .server import start_thread

    try:
        global server_port
        server_port = get_free_port()
        start_thread(server_port)
    except Exception:
        raise Exception('The server could not be started.')


class Instance:
    def __init__(self, license_key: str):
        self.id = str(uuid.uuid4()).split('-')[0]
        self.session = requests.Session()
        retry_adapter = requests.adapters.HTTPAdapter(max_retries=5)
        self.session.mount('http://', retry_adapter)
        self.items = []
        self.license_key = license_key
        self.live = False

    def send(self, id: str, command: str, arguments: dict = None):
        if not self.live:
            self.items.append(
                {'id': str(id), 'command': command, 'args': arguments or {}}
            )
        else:
            binary_data = msgpack.packb(
                {'id': str(id), 'command': command, 'args': arguments}
            )
            try:
                response = self.session.post(
                    f'http://{LOCALHOST}:{server_port}/item?id={self.id}',
                    data=binary_data,
                    headers={'Content-Type': 'application/msgpack'},
                )
                if response.ok:
                    return True
            except requests.RequestException as e:
                print(e)

    def open_in_browser(self):
        if not self.live:
            start_server()
            self.live = True
            for i in self.items:
                self.send(i['id'], i['command'], i['args'])

        try:
            response = self.session.post(
                url=f'http://{LOCALHOST}:{server_port}/setLicense',
                data=msgpack.packb({'license': self.license_key}),
                headers={'Content-Type': 'application/msgpack'},
            )
            if response.ok:
                webbrowser.open(f'http://{LOCALHOST}:{server_port}/?id={self.id}')
        except requests.exceptions.ConnectionError as e:
            print(e)

    def open_in_notebook(self, width: int | str = '100%', height: int | str = 600):
        if not self.live:
            start_server()
            self.live = True
            for i in self.items:
                self.send(i['id'], i['command'], i['args'])

        try:
            response = self.session.post(
                url=f'http://{LOCALHOST}:{server_port}/setLicense',
                data=msgpack.packb({'license': self.license_key}),
                headers={'Content-Type': 'application/msgpack'},
            )
            if response.ok:
                return display(
                    IFrame(
                        src=f'http://{LOCALHOST}:{server_port}/?id={self.id}',
                        width=width,
                        height=height,
                    )
                )
        except requests.exceptions.ConnectionError as e:
            print(e)

    def close(self):
        """
        Close the connection to the Trader application.
        Note: This will terminate the current Python instance!
        """
        if self.live:
            self.send(self.id, 'shutdown')
