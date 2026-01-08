import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from loguru import logger

from currency_exchange.dtos import (
    CurrencyDto,
    CurrencyPostDto,
    ExchangeDto,
    ExchangePostDto,
    RateDto,
    RatePostUpdateDto,
)
from currency_exchange.exceptions import (
    CantConvertError,
    CurrencyAlreadyExistsError,
    CurrencyExchangeError,
    NoCurrencyError,
    NoCurrencyPairError,
    NoRateError,
    RateAlreadyExistsError,
)
from currency_exchange.service import Service


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        first_segment = self.get_first_path_segment()
        number_of_segments = self.get_number_of_path_segments()

        if first_segment == 'currencies' and number_of_segments == 1:
            self.get_currencies()

        elif first_segment == 'currency':
            if number_of_segments == 1:
                self.send_error(HTTPStatus.BAD_REQUEST)
            elif number_of_segments == 2:
                cur_code = self.get_second_path_segment()
                self.get_currency(cur_code) if self.is_valid_cur_code(
                    cur_code
                ) else self.send_error(HTTPStatus.BAD_REQUEST)

        elif first_segment == 'exchangeRates' and number_of_segments == 1:
            self.get_rates()

        elif first_segment == 'exchangeRate':
            if number_of_segments == 1:
                self.send_error(HTTPStatus.BAD_REQUEST)
            elif number_of_segments == 2:
                code_pair = self.get_second_path_segment()
                self.get_rate(code_pair) if self.is_valid_pair(
                    code_pair
                ) else self.send_error(HTTPStatus.BAD_REQUEST)

        elif first_segment == 'exchange':
            params = self.get_query_params()
            from_lst = params.get('from')
            to_lst = params.get('to')
            amount_lst = params.get('amount')
            if (
                from_lst is not None
                and to_lst is not None
                and amount_lst is not None
                and self.is_valid_cur_code(from_lst[0])
                and self.is_valid_cur_code(to_lst[0])
                and RequestHandler.is_valid_amount(amount_lst[0])
            ):
                self.exchange_currencies(from_lst[0], to_lst[0], float(amount_lst[0]))
            else:
                self.send_error(HTTPStatus.BAD_REQUEST)

        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        first_segment = self.get_first_path_segment()
        number_of_segments = self.get_number_of_path_segments()

        if first_segment == 'currencies' and number_of_segments == 1:
            params = self.get_request_params()
            name_lst = params.get('name')
            code_lst = params.get('code')
            sign_lst = params.get('sign')
            if name_lst is not None and code_lst is not None and sign_lst is not None:
                self.save_currency(name_lst[0], code_lst[0], sign_lst[0])
            else:
                self.send_error(HTTPStatus.BAD_REQUEST)

        elif first_segment == 'exchangeRates' and number_of_segments == 1:
            params = self.get_request_params()
            base_currency_code_lst = params.get('baseCurrencyCode')
            target_currency_code_lst = params.get('targetCurrencyCode')
            rate_lst = params.get('rate')
            if (
                base_currency_code_lst is not None
                and target_currency_code_lst is not None
                and rate_lst is not None
            ):
                self.save_rate(
                    base_currency_code_lst[0],
                    target_currency_code_lst[0],
                    float(rate_lst[0]),
                )
            else:
                self.send_error(HTTPStatus.BAD_REQUEST)

        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:
        number_of_segments = self.get_number_of_path_segments()

        if self.get_first_path_segment() == 'exchangeRate':
            if number_of_segments == 1:
                self.send_error(HTTPStatus.BAD_REQUEST)
            elif number_of_segments == 2:
                code_pair = self.get_second_path_segment()

                params = self.get_request_params()
                rate_lst = params.get('rate')

                self.update_rate(code_pair, float(rate_lst[0])) if self.is_valid_pair(
                    code_pair
                ) and rate_lst is not None else self.send_error(HTTPStatus.BAD_REQUEST)

        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def get_service(self) -> Service:
        return Service()

    def get_currencies(self) -> None:
        service = self.get_service()
        try:
            self.send_ok(HTTPStatus.OK, service.get_all_currencies())
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def get_currency(self, cur_code: str) -> None:
        service = self.get_service()
        try:
            self.send_ok(HTTPStatus.OK, service.get_currency_with_code(cur_code))
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except NoCurrencyError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def get_rates(self) -> None:
        service = self.get_service()
        try:
            self.send_ok(HTTPStatus.OK, service.get_all_rates())
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def get_rate(self, code_pair: str) -> None:
        service = self.get_service()
        try:
            self.send_ok(HTTPStatus.OK, service.get_rate(code_pair))
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except (NoCurrencyError, NoRateError):
            self.send_error(HTTPStatus.NOT_FOUND)

    def save_currency(self, name: str, code: str, sign: str) -> None:
        service = self.get_service()

        try:
            self.send_ok(
                HTTPStatus.CREATED,
                service.save_currency(CurrencyPostDto(name, code, sign)),
            )
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST)
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except CurrencyAlreadyExistsError:
            self.send_error(HTTPStatus.CONFLICT)

    def save_rate(
        self, base_currency_code: str, target_currency_code: str, rate: float
    ) -> None:
        service = self.get_service()

        try:
            self.send_ok(
                HTTPStatus.CREATED,
                service.save_rate(
                    RatePostUpdateDto(base_currency_code, target_currency_code, rate)
                ),
            )
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST)
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except NoCurrencyError:
            self.send_error(HTTPStatus.NOT_FOUND)
        except RateAlreadyExistsError:
            self.send_error(HTTPStatus.CONFLICT)

    def update_rate(self, code_pair: str, rate: float) -> None:
        service = self.get_service()

        try:
            self.send_ok(
                HTTPStatus.OK,
                service.update_rate(
                    RatePostUpdateDto(code_pair[:3], code_pair[3:], rate)
                ),
            )
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST)
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except NoCurrencyPairError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def exchange_currencies(
        self, from_cur_code: str, to_cur_code: str, amount: float
    ) -> None:
        service = self.get_service()

        try:
            self.send_ok(
                HTTPStatus.OK,
                service.exchange_currencies(
                    ExchangePostDto(from_cur_code, to_cur_code, amount)
                ),
            )
        except CurrencyExchangeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
        except CantConvertError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def get_request_params(self) -> dict[str, Any]:
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        return parse_qs(data_string.decode())

    def get_query_params(self) -> dict[str, Any]:
        parsed_path = urlparse(self.path)
        return parse_qs(parsed_path.query)

    def is_valid_pair(self, code_pair: str) -> bool:
        return (
            code_pair.isalpha()
            and code_pair.isascii()
            and code_pair.isupper()
            and len(code_pair) == 6
        )

    def is_valid_cur_code(self, cur_code: str) -> bool:
        return (
            cur_code.isalpha()
            and cur_code.isascii()
            and cur_code.isupper()
            and len(cur_code) == 3
        )

    @staticmethod
    def is_valid_amount(str_amount: str) -> bool:
        if RequestHandler.is_amount_could_be_float(str_amount):
            return float(str_amount) > 0
        else:
            return False

    @staticmethod
    def is_amount_could_be_float(str_amount: str) -> bool:
        try:
            float(str_amount)
            return True
        except ValueError:
            return False

    def send_ok(
        self,
        code: int,
        data: CurrencyDto | RateDto | ExchangeDto | list[CurrencyDto] | list[RateDto],
    ) -> None:
        body = self.prepare_body(data)
        self.send_headers(code, body)
        self.wfile.write(body)

    def prepare_body(
        self,
        data: CurrencyDto | RateDto | ExchangeDto | list[CurrencyDto] | list[RateDto],
    ) -> bytes:
        if isinstance(data, (CurrencyDto, RateDto, ExchangeDto)):
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
