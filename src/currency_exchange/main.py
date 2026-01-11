import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from loguru import logger

from currency_exchange.dtos import (
    CurrencyPostDto,
    ExchangePostDto,
    RatePostUpdateDto,
)
from currency_exchange.exceptions import (
    CantConvertError,
    CurrencyAlreadyExistsError,
    InvalidDataError,
    NoCurrencyError,
    NoCurrencyPairError,
    NoDataBaseConnectionError,
    NoRateError,
    RateAlreadyExistsError,
)
from currency_exchange.service import Service
from currency_exchange.utils.string_helpers import serialize_response


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        first_segment = self.get_first_path_segment()
        number_of_segments = self.get_number_of_path_segments()

        if first_segment == 'currencies' and number_of_segments == 1:
            self.get_currencies()

        elif first_segment == 'currency':
            if number_of_segments == 1:
                self.send_error(
                    HTTPStatus.BAD_REQUEST, 'Код валюты отсутствует в адресе'
                )
            elif number_of_segments == 2:
                cur_code = self.get_second_path_segment()
                self.get_currency(cur_code)

        elif first_segment == 'exchangeRates' and number_of_segments == 1:
            self.get_rates()

        elif first_segment == 'exchangeRate':
            if number_of_segments == 1:
                self.send_error(
                    HTTPStatus.BAD_REQUEST, 'Коды валют пары отсутствуют в адресе'
                )
            elif number_of_segments == 2:
                code_pair = self.get_second_path_segment()
                self.get_rate(code_pair)

        elif first_segment == 'exchange':
            params = self.get_query_params()
            from_lst = params.get('from')
            to_lst = params.get('to')
            amount_lst = params.get('amount')
            if from_lst is not None and to_lst is not None and amount_lst is not None:
                self.exchange(from_lst[0], to_lst[0], float(amount_lst[0]))
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
                self.create_currency(name_lst[0], code_lst[0], sign_lst[0])
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, 'Отсутствует нужное поле формы')

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
                self.create_rate(
                    base_currency_code_lst[0],
                    target_currency_code_lst[0],
                    float(rate_lst[0]),
                )
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, 'Отсутствует нужное поле формы')

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
                if rate_lst is not None:
                    self.update_rate(code_pair, float(rate_lst[0]))

        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def get_currencies(self) -> None:
        service = self.get_service()
        try:
            api_response = serialize_response(service.get_all_currencies())
            self.send_json_response(HTTPStatus.OK, api_response)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')

    def get_currency(self, cur_code: str) -> None:
        service = self.get_service()
        try:
            api_response = serialize_response(service.get_currency_with_code(cur_code))
            self.send_json_response(HTTPStatus.OK, api_response)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except NoCurrencyError:
            self.send_error(HTTPStatus.NOT_FOUND, 'Валюта не найдена')

    def get_rates(self) -> None:
        service = self.get_service()
        try:
            api_response = serialize_response(service.get_all_rates())
            self.send_json_response(HTTPStatus.OK, api_response)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')

    def get_rate(self, code_pair: str) -> None:
        service = self.get_service()
        try:
            api_response = serialize_response(service.get_rate(code_pair))
            self.send_json_response(HTTPStatus.OK, api_response)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except (NoCurrencyError, NoRateError):
            self.send_error(HTTPStatus.NOT_FOUND, 'Обменный курс для пары не найден')

    def create_currency(self, name: str, code: str, sign: str) -> None:
        service = self.get_service()

        try:
            api_response = serialize_response(
                service.save_currency(CurrencyPostDto(name, code, sign))
            )
            self.send_json_response(
                HTTPStatus.CREATED,
                api_response,
            )
        except ValueError as error:
            self.send_error(HTTPStatus.BAD_REQUEST, f'{error}')
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except CurrencyAlreadyExistsError:
            self.send_error(HTTPStatus.CONFLICT, 'Валюта с таким кодом уже существует')

    def create_rate(
        self, base_currency_code: str, target_currency_code: str, rate: float
    ) -> None:
        service = self.get_service()

        try:
            api_response = serialize_response(
                service.save_rate(
                    RatePostUpdateDto(base_currency_code, target_currency_code, rate)
                )
            )
            self.send_json_response(
                HTTPStatus.CREATED,
                api_response,
            )
        except ValueError as error:
            self.send_error(HTTPStatus.BAD_REQUEST, f'{error}')
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except NoCurrencyError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                'Одна (или обе) валюта из валютной пары не существует в БД',
            )
        except RateAlreadyExistsError:
            self.send_error(
                HTTPStatus.CONFLICT, 'Валютная пара с таким кодом уже существует'
            )
        except InvalidDataError:
            self.send_error(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                'code must be 3 uppercase English letters',
            )

    def update_rate(self, code_pair: str, rate: float) -> None:
        service = self.get_service()

        try:
            api_response = serialize_response(
                service.update_rate(
                    RatePostUpdateDto(code_pair[:3], code_pair[3:], rate)
                )
            )
            self.send_json_response(
                HTTPStatus.OK,
                api_response,
            )
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except NoCurrencyPairError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def exchange(self, from_cur_code: str, to_cur_code: str, amount: float) -> None:
        service = self.get_service()

        try:
            api_response = serialize_response(
                service.exchange_currencies(
                    ExchangePostDto(from_cur_code, to_cur_code, amount)
                )
            )
            self.send_json_response(
                HTTPStatus.OK,
                api_response,
            )
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except CantConvertError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def send_json_response(self, status_code: int, api_response: str) -> None:
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(api_response)))
        self.end_headers()
        self.wfile.write(api_response.encode('utf-8'))

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        try:
            shortmsg, longmsg = self.responses[code]
        except KeyError:
            shortmsg, longmsg = '???', '???'

        actual_status_message = shortmsg

        if message is None:
            message = shortmsg
        if explain is None:
            explain = longmsg
        self.log_error('code %d, message %s', code, message)
        self.send_response(code, actual_status_message)
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
            content = {'message': message}
            body = json.dumps(content, ensure_ascii=False).encode('utf-8')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()

        if self.command != 'HEAD' and body:
            self.wfile.write(body)

    def get_service(self) -> Service:
        return Service()

    def get_request_params(self) -> dict[str, Any]:
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        return parse_qs(data_string.decode())

    def get_query_params(self) -> dict[str, Any]:
        parsed_path = urlparse(self.path)
        return parse_qs(parsed_path.query)

    def get_first_path_segment(self) -> str:
        return self.path.strip('/').split('/')[0].split('?')[0]

    def get_second_path_segment(self) -> str:
        return self.path.strip('/').split('/')[1]

    def get_number_of_path_segments(self) -> int:
        return len(self.path.strip('/').split('/'))


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
