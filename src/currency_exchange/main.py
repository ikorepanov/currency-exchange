import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from sqlite3 import connect
from typing import Any

from loguru import logger

from currency_exchange.models import Currency


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        # Controller
        # A kind of validation
        first_segment = self.get_first_path_segment()
        number_of_segments = self.get_number_of_path_segments()

        if first_segment == 'currencies' and number_of_segments == 1:
            self.read_currencies()
        elif first_segment == 'currency':
            self.read_currency()
        elif first_segment == 'exchangeRates':
            self.read_rates()
        elif first_segment == 'exchangeRate':
            self.read_rate()
        elif first_segment == 'exchange':
            self.exchange_currencies()
        elif first_segment == '':
            self.root()
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        first_segment = self.get_first_path_segment()

        if first_segment == 'currencies':
            self.save_currency()
        elif first_segment == 'exchangeRates':
            self.save_rate()
        else:
            self.send_custom_error(404)

    def do_PATCH(self) -> None:
        if self.get_first_path_segment() == 'exchangeRate':
            self.update_rate()
        else:
            self.send_custom_error(404)

    def read_currencies(self) -> None:
        # DAO
        conn = connect('./src/currency_exchange/db.sqlite')
        cur = conn.cursor()
        sql = 'SELECT * FROM Currencies'
        cur.execute(sql)
        raw_data = cur.fetchall()
        cur.close()

        result = []
        for data in raw_data:
            entity = Currency(data[0], data[2], data[1], data[3])
            result.append(entity)

        # Controller
        json_string = [ob.__dict__ for ob in result]
        body = json.dumps(json_string, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_currency(self) -> None:
        pass

    def read_rates(self) -> None:
        pass

    def read_rate(self) -> None:
        pass

    def exchange_currencies(self) -> None:
        pass

    def save_currency(self) -> None:
        pass

    def save_rate(self) -> None:
        pass

    def update_rate(self) -> None:
        pass

    def send_custom_error(self, code: int) -> None:
        pass

    def get_first_path_segment(self) -> str:
        return self.path.strip('/').split('/')[0].split('?')[0]

    def get_number_of_path_segments(self) -> int:
        return len(self.path.strip('/').split('/'))

    def root(self) -> None:
        data = self.retrieve_data()
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def retrieve_data(self) -> dict[str, Any]:
        return {'id': 0, 'name': 'Euro', 'code': 'EUR', 'sign': '€'}


class ExchangeServer(HTTPServer):
    """Переопределяем HTTPServer, т.к. впоследствии добавим self.db = db."""

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: type[RequestHandler],
        bind_and_activate: bool = True,
    ) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)


def start_server(
    addr: str,
    port: int,
    server_class: type[HTTPServer] = ExchangeServer,
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
