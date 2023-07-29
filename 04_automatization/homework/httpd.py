import os
import posixpath
import socket
import threading
from argparse import ArgumentParser
from datetime import datetime
from queue import Queue
from urllib.parse import unquote

from constants import EXT_TO_MIME, ERRORS, ERROR_MSG_TEMPLATE, INDEX_FILE, BAD_REQUEST, ALLOWED_METHODS, \
    INTERNAL_ERROR, METHOD_NOT_ALLOWED, NOT_FOUND, OK
from logger import logger


class HTTPServer:
    server_name = 'OTUServer'

    def __init__(self, host: str, port: int, workers: int, root_dir: str):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.workers = workers
        self.root_dir = root_dir
        self.request_queue = Queue(maxsize=self.workers)
        self.request_handler_class = RequestHandler
        self.is_shut_down = threading.Event()
        self.__shutdown_request = False

    def shutdown(self):
        self.__shutdown_request = True
        self.is_shut_down.wait()

    def serve_forever(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.workers)
        logger.info(f'Server started at {self.host}:{self.port}')
        self.is_shut_down.clear()
        for _ in range(self.workers):
            thread = threading.Thread(target=self.process_request)
            thread.start()

        while not self.__shutdown_request:
            try:
                connection = self.socket.accept()
                if connection:
                    self.request_queue.put(connection)
            except Exception as ex:
                logger.error(ex)

    def process_request(self):
        try:
            handler = self.request_handler_class(self)
            handler.process()
        except Exception as e:
            logger.error(e)


class RequestHandler:
    max_request_line_size = 64 * 1024
    max_headers = 100

    def __init__(self, server: HTTPServer):
        self.server = server
        self.client_address = None
        self.headers = []
        self.read_file = None
        self.write_file = None
        self.raw_request = None
        self.request = ''
        self.request_version = ''
        self.request_method = ''
        self.request_path = ''
        self.request_headers = {}

    def process(self):
        requests_queue = self.server.request_queue
        shutdown_event = self.server.is_shut_down
        while True:
            try:
                if shutdown_event.is_set():
                    break
                connection = requests_queue.get()
                if connection is None:
                    requests_queue.task_done()
                    break
                sock, self.client_address = connection
                self.read_file = sock.makefile('rb')
                self.write_file = sock.makefile('wb')
                try:
                    self.handle_request()
                except Exception as err:
                    logger.error(err)
                finally:
                    requests_queue.task_done()
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
            except Exception as err:
                logger.error(err)

    def handle_request(self):
        try:
            self.raw_request = self.read_file.readline(self.max_request_line_size + 1)
            if not self.raw_request:
                return
            if len(self.raw_request) > self.max_request_line_size:
                self.error_response(BAD_REQUEST)
                return
            if not self.parse_request():
                return

            client_address, client_port = self.client_address
            logger.info(f'{client_address}:{client_port} - {self.request}')
            if self.request_method not in ALLOWED_METHODS:
                self.error_response(METHOD_NOT_ALLOWED)
                return
            handle_method = self.__getattribute__(self.request_method.lower())
            handle_method()
            self.write_file.flush()

        except Exception as err:
            logger.error(err)

    def error_response(self, code: int):
        message = ERRORS[code]
        content = ERROR_MSG_TEMPLATE.format(code, message).encode()

        self.add_default_headers(code, message)
        self.add_header('Connection', 'close')
        self.add_header('Content-Type', 'text/html;charset=utf-8')
        self.add_header('Content-Length', str(len(content)))
        self.complete_headers()

        if self.request_method != 'HEAD':
            self.write_file.write(content)
        self.write_file.flush()

    @staticmethod
    def get_datetime_str():
        return datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')

    @staticmethod
    def get_file_type(path):
        _, ext = posixpath.splitext(path)
        return EXT_TO_MIME.get(ext.lower(), 'application/octet-stream')

    def add_default_headers(self, code: int, msg: str = ''):
        self.headers.append(f'HTTP/1.1 {code} {msg}\r\n'.encode())
        self.add_header('Server', self.server.server_name)
        self.add_header('Date', self.get_datetime_str())

    def add_header(self, key, value):
        self.headers.append(f'{key}: {value}\r\n'.encode())

    def complete_headers(self):
        self.headers.append(b'\r\n')
        self.write_file.write(b''.join(self.headers))
        self.headers = []

    def parse_request(self):
        request = self.raw_request.decode('iso-8859-1')
        request = request.rstrip('\r\n')
        self.request = request
        request_parts = request.split()
        if not request_parts:
            return False
        if len(request_parts) == 3:
            self.request_method, self.request_path, self.request_version = request_parts
            if self.request_version != 'HTTP/1.1':
                self.error_response(BAD_REQUEST)
                return False
        try:
            self._read_headers(self.read_file)
        except ValueError:
            self.error_response(BAD_REQUEST)
            return False
        return True

    def _read_headers(self, read_file):
        headers = []
        while True:
            line = read_file.readline(self.max_request_line_size + 1)
            if len(line) > self.max_request_line_size:
                raise ValueError('Too long header line')
            headers.append(line)
            if len(headers) > self.max_headers:
                raise ValueError('Too many headers')
            if line in (b'\r\n', b'\n', b''):
                break
        for line in headers:
            line = line.rstrip(b'\r\n').decode('latin-1')
            value = line.split(':')
            if len(value) != 2:
                continue
            self.request_headers[value[0]] = value[1]

    def get(self):
        content = self.make_response()
        if content:
            self.write_file.write(content)

    def head(self):
        self.make_response()

    def make_response(self):
        path = self.translate_path(self.request_path)
        if os.path.isdir(path):
            index_path = os.path.join(path, INDEX_FILE)
            if os.path.exists(index_path):
                path = index_path
            else:
                self.error_response(NOT_FOUND)
                return
        if path.endswith('/'):
            self.error_response(NOT_FOUND)
            return

        if os.path.exists(path):
            mime_type = self.get_file_type(path)
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    self.add_default_headers(OK, 'OK')
                    self.add_header('Content-type', mime_type)
                    self.add_header('Content-Length', len(content))
                    self.complete_headers()
                    return content

            except Exception as err:
                logger.error(err)
                self.error_response(INTERNAL_ERROR)
        else:
            self.error_response(NOT_FOUND)

    def translate_path(self, path: str):
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        has_trailing_slash = path.rstrip().endswith('/')
        if '%' in path:
            path = unquote(path)
        path = posixpath.normpath(path)
        path_parts = path.split('/')
        path_parts = filter(None, path_parts)
        spath = os.path.abspath(self.server.root_dir)
        for part in path_parts:
            if os.path.dirname(part) or part in (os.curdir, os.pardir):
                continue
            spath = os.path.join(spath, part)
        if has_trailing_slash:
            spath += '/'
        return spath


if __name__ == '__main__':
    args_parser = ArgumentParser(add_help=False)
    args_parser.add_argument('-h', '--host', default='localhost')
    args_parser.add_argument('-p', '--port', type=int, default=8080)
    args_parser.add_argument('-w', '--workers', type=int, default=42)
    args_parser.add_argument('-r', '--root', default='.')
    args = args_parser.parse_args()

    http_server = HTTPServer(
        args.host,
        args.port,
        args.workers,
        args.root
    )
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.shutdown()
