from http.server import BaseHTTPRequestHandler, HTTPServer

from loguru import logger

from currency_exchange.mvc_layers.controller import RequestHandler


def start_server(
    addr: str,
    port: int,
    server_class: type[HTTPServer] = HTTPServer,
    handler_class: type[BaseHTTPRequestHandler] = RequestHandler,
) -> None:
    server_address = (addr, port)

    with server_class(server_address, handler_class) as httpd:
        logger.info(f'Serving at {addr}:{port}')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()


def main() -> None:
    start_server('127.0.0.1', 8000)


if __name__ == '__main__':
    main()
