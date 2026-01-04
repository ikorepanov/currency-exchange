import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from loguru import logger

from currency_exchange.exceptions import CurrencyExchangeError, NoCurrencyError
from currency_exchange.models import Currency, Rate
from currency_exchange.services import RateService
from currency_exchange.storages import CurrencyStorage, RateStorage


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        first_segment = self.get_first_path_segment()
        number_of_segments = self.get_number_of_path_segments()

        currency_storage = CurrencyStorage()

        rate_service = RateService()

        if first_segment == 'currencies' and number_of_segments == 1:
            self.read_all_entities_from(currency_storage)
        elif first_segment == 'currency':
            if number_of_segments == 1:
                self.send_error(HTTPStatus.BAD_REQUEST)
            elif number_of_segments == 2:
                cur_code = self.get_second_path_segment()
                self.read_currency(currency_storage, cur_code)
        elif first_segment == 'exchangeRates' and number_of_segments == 1:
            self.read_all_rates_with(rate_service)
        elif first_segment == 'exchangeRate':
            self.read_rate()
        elif first_segment == 'exchange':
            self.exchange_currencies()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        first_segment = self.get_first_path_segment()

        if first_segment == 'currencies':
            self.save_currency()
        elif first_segment == 'exchangeRates':
            self.save_rate()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:
        if self.get_first_path_segment() == 'exchangeRate':
            self.update_rate()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def read_all_entities_from(self, storage: CurrencyStorage | RateStorage) -> None:
        try:
            self.send_ok(storage.load_all())
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def read_all_rates_with(self, service: RateService) -> None:
        try:
            self.send_ok(service.load_all_rates())
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def read_currency(self, storage: CurrencyStorage, cur_code: str) -> None:
        try:
            currency_object = storage.load_one(cur_code)
            self.send_ok(currency_object)
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except NoCurrencyError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def send_ok(self, data: Currency | Rate | list[Currency] | list[Rate]) -> None:
        body = self.prepare_body(data)
        self.send_headers(HTTPStatus.OK, body)
        self.wfile.write(body)

    def prepare_body(
        self, data: Currency | Rate | list[Currency] | list[Rate]
    ) -> bytes:
        if isinstance(data, (Currency, Rate)):
            return json.dumps(
                self.change_keys_for_json(asdict(data)), ensure_ascii=False
            ).encode('utf-8')
        else:
            return json.dumps(
                [self.change_keys_for_json(asdict(obj)) for obj in data],
                ensure_ascii=False,
            ).encode('utf-8')

    def change_keys_for_json(
        self, original_dictionary: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            (
                self.to_lower_camel_case(key)
                if key in ('base_currency', 'target_currency')
                else key
            ): value
            for key, value in original_dictionary.items()
        }

    def to_lower_camel_case(self, snake_str: str) -> str:
        camel_string = self.to_camel_case(snake_str)
        return snake_str[0].lower() + camel_string[1:]

    def to_camel_case(self, snake_str: str) -> str:
        return ''.join(letter.capitalize() for letter in snake_str.lower().split('_'))

    def send_headers(self, code: int, body: bytes) -> None:
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()

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

    def get_first_path_segment(self) -> str:
        return self.path.strip('/').split('/')[0].split('?')[0]

    def get_second_path_segment(self) -> str:
        return self.path.strip('/').split('/')[1]

    def get_number_of_path_segments(self) -> int:
        return len(self.path.strip('/').split('/'))

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        try:
            shortmsg, longmsg = self.responses[code]
        except KeyError:
            shortmsg, longmsg = '???', '???'
        if message is None:
            message = shortmsg
        if explain is None:
            explain = longmsg
        self.log_error('code %d, message %s', code, message)
        self.send_response(code, message)
        self.send_header('Connection', 'close')

        # Message body is omitted for cases described in:
        #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
        #  - RFC7231: 6.3.6. 205(Reset Content)
        body = None
        if code >= 200 and code not in (
            HTTPStatus.NO_CONTENT,
            HTTPStatus.RESET_CONTENT,
            HTTPStatus.NOT_MODIFIED,
        ):
            content = {'message': message, 'explain': explain}
            body = json.dumps(content).encode('utf-8')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()

        if self.command != 'HEAD' and body:
            self.wfile.write(body)


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
