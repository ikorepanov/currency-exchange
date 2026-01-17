import json
from functools import cached_property
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import ParseResult, parse_qsl, unquote, urlparse

from currency_exchange.dtos import CurrencyPostDto
from currency_exchange.exceptions import (
    CantConvertError,
    CurrencyAlreadyExistsError,
    NoCurrencyError,
    NoCurrencyPairError,
    NoDataBaseConnectionError,
    NoRateError,
    RateAlreadyExistsError,
)
from currency_exchange.mvc_layers.service import Service
from currency_exchange.utils.string_helpers import serialize
from currency_exchange.utils.validation import (
    is_valid_amount,
    is_valid_cur_code,
    is_valid_name,
    is_valid_sign,
)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.first_segment == 'currencies':
            self.get_currencies()

        elif self.first_segment == 'currency':
            self.get_currency()

        elif self.first_segment == 'exchangeRates':
            self.get_rates()

        elif self.first_segment == 'exchangeRate':
            self.get_rate()

        elif self.first_segment == 'exchange':
            self.exchange()

        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')

    def do_POST(self) -> None:
        if self.first_segment == 'currencies':
            self.create_currency()

        elif self.first_segment == 'exchangeRates':
            self.create_rate()

        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')

    def do_PATCH(self) -> None:
        if self.first_segment == 'exchangeRate':
            self.update_rate()

        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')

    def get_currencies(self) -> None:
        if len(self.path_segments) == 1:
            try:
                data = self.service.get_currencies()
                response = serialize(data)
                self.send_json_response(HTTPStatus.OK, response)
            except NoDataBaseConnectionError as error:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def get_currency(self) -> None:
        if self.second_segment is None:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Код валюты отсутствует в адресе')
        elif len(self.path_segments) == 2:
            cur_code = self.second_segment

            if not is_valid_cur_code(cur_code):
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Код валюты должен состоять из 3 заглавных английских букв',
                )
            else:
                try:
                    data = self.service.get_currency(cur_code)
                    response = serialize(data)
                    self.send_json_response(HTTPStatus.OK, response)
                except NoDataBaseConnectionError as error:
                    self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                except NoCurrencyError as error:
                    self.send_error(HTTPStatus.NOT_FOUND, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def get_rates(self) -> None:
        if len(self.path_segments) == 1:
            try:
                data = self.service.get_rates()
                response = serialize(data)
                self.send_json_response(HTTPStatus.OK, response)
            except NoDataBaseConnectionError as error:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def get_rate(self) -> None:
        if self.second_segment is None:
            self.send_error(
                HTTPStatus.BAD_REQUEST, 'Коды валют пары отсутствуют в адресе'
            )
        elif len(self.path_segments) == 2:
            code_pair = self.second_segment
            base_cur_code = self.second_segment[:3]
            target_cur_code = self.second_segment[3:]

            if not (
                is_valid_cur_code(base_cur_code) and is_valid_cur_code(target_cur_code)
            ):
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Пара кодов валют должна состоять из 6 заглавных английских букв',
                )
            elif base_cur_code == target_cur_code:
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Нельзя получить обменный курс валюты на саму себя',
                )
            else:
                try:
                    data = self.service.get_rate(code_pair)
                    response = serialize(data)
                    self.send_json_response(HTTPStatus.OK, response)
                except NoDataBaseConnectionError as error:
                    self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                except NoRateError as error:
                    self.send_error(HTTPStatus.NOT_FOUND, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def create_currency(self) -> None:
        if len(self.path_segments) == 1:
            cur_name = self.request_params.get('name')
            cur_code = self.request_params.get('code')
            cur_sign = self.request_params.get('sign')

            if cur_name is None or cur_code is None or cur_sign is None:
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Отсутствует нужное поле формы',
                )
            else:
                if not is_valid_name(cur_name):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Имя валюты должно начинаться с заглавной буквы '
                        'и состоять из букв английского алфавита',
                    )
                elif not is_valid_cur_code(cur_code):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Код валюты должен состоять из 3 заглавных английских букв',
                    )
                elif not is_valid_sign(cur_sign):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Знак валюты должен быть специальным Unicode-символом '
                        'категории Currency_Symbol',
                    )
                else:
                    try:
                        currency_post_dto = CurrencyPostDto(
                            cur_name, cur_code, cur_sign
                        )
                        data = self.service.create_currency(currency_post_dto)
                        response = serialize(data)
                        self.send_json_response(HTTPStatus.CREATED, response)
                    except NoDataBaseConnectionError as error:
                        self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                    except CurrencyAlreadyExistsError as error:
                        self.send_error(HTTPStatus.CONFLICT, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def create_rate(self) -> None:
        if len(self.path_segments) == 1:
            base_cur_code = self.request_params.get('baseCurrencyCode')
            target_cur_code = self.request_params.get('targetCurrencyCode')
            exch_rate = self.request_params.get('rate')

            if base_cur_code is None or target_cur_code is None or exch_rate is None:
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Отсутствует нужное поле формы',
                )
            else:
                if not (
                    is_valid_cur_code(base_cur_code)
                    and is_valid_cur_code(target_cur_code)
                ):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Код валюты должен состоять из 3 заглавных английских букв',
                    )
                elif not is_valid_amount(exch_rate):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Обменный курс должен быть представлен целым числом '
                        'или числом с плавающей точкой с не более чем шестью '
                        'десятичными знаками',
                    )
                elif base_cur_code == target_cur_code:
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Нельзя добавить обменный курс валюты на саму себя',
                    )
                else:
                    try:
                        data = self.service.create_rate(
                            base_cur_code, target_cur_code, exch_rate
                        )
                        response = serialize(data)
                        self.send_json_response(
                            HTTPStatus.CREATED,
                            response,
                        )
                    except NoDataBaseConnectionError as error:
                        self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                    except NoCurrencyPairError as error:
                        self.send_error(HTTPStatus.NOT_FOUND, str(error))
                    except RateAlreadyExistsError as error:
                        self.send_error(HTTPStatus.CONFLICT, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def update_rate(self) -> None:
        if self.second_segment is None:
            self.send_error(
                HTTPStatus.BAD_REQUEST, 'Коды валют пары отсутствуют в адресе'
            )
        elif len(self.path_segments) == 2:
            code_pair = self.second_segment
            base_cur_code = self.second_segment[:3]
            target_cur_code = self.second_segment[3:]
            exch_rate = self.request_params.get('rate')

            if exch_rate is None:
                self.send_error(HTTPStatus.BAD_REQUEST, 'Отсутствует нужное поле формы')

            else:
                if not (
                    is_valid_cur_code(base_cur_code)
                    and is_valid_cur_code(target_cur_code)
                ):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Пара кодов валют должна состоять '
                        'из 6 заглавных английских букв',
                    )
                elif not is_valid_amount(exch_rate):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Обменный курс должен быть представлен целым числом '
                        'или числом с плавающей точкой с не более чем шестью '
                        'десятичными знаками',
                    )
                elif base_cur_code == target_cur_code:
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Нельзя обновить обменный курс валюты на саму себя',
                    )
                else:
                    try:
                        data = self.service.update_rate(code_pair, exch_rate)
                        response = serialize(data)
                        self.send_json_response(HTTPStatus.OK, response)
                    except NoDataBaseConnectionError as error:
                        self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                    except NoRateError as error:
                        self.send_error(HTTPStatus.NOT_FOUND, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def exchange(self) -> None:
        if len(self.path_segments) == 1:
            from_cur_code = self.query_params.get('from')
            to_cur_code = self.query_params.get('to')
            amount = self.query_params.get('amount')

            if from_cur_code is None or to_cur_code is None or amount is None:
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Отсутствует один или несколько нужных параметров запроса',
                )
            else:
                if not is_valid_cur_code(from_cur_code) or not is_valid_cur_code(
                    to_cur_code
                ):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Код валюты должен состоять из 3 заглавных английских букв',
                    )
                elif not is_valid_amount(amount):
                    self.send_error(
                        HTTPStatus.BAD_REQUEST,
                        'Количество средств для рассчёта перевода '
                        'должно быть положительным числом',
                    )
                else:
                    try:
                        data = self.service.exchange_currencies(
                            from_cur_code, to_cur_code, float(amount)
                        )
                        response = serialize(data)
                        self.send_json_response(HTTPStatus.OK, response)
                    except NoDataBaseConnectionError as error:
                        self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                    except CantConvertError as error:
                        self.send_error(HTTPStatus.NOT_FOUND, str(error))
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Неправильный формат запроса')

    def send_json_response(self, status_code: int, response: str) -> None:
        body = response.encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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

    @cached_property
    def service(self) -> Service:
        return Service()

    @cached_property
    def parsed_path(self) -> ParseResult:
        return urlparse(self.path)

    @cached_property
    def path_segments(self) -> list[str]:
        return self.parsed_path.path.strip('/').split('/')

    @cached_property
    def first_segment(self) -> str:
        return self.path_segments[0]

    @cached_property
    def second_segment(self) -> str | None:
        try:
            encoded = self.path_segments[1]
            return unquote(encoded, encoding='utf-8')
        except IndexError:
            return None

    @cached_property
    def request_params(self) -> dict[str, Any]:
        data_string = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        return dict(parse_qsl(data_string.decode('utf-8')))

    @cached_property
    def query_params(self) -> dict[str, Any]:
        return dict(parse_qsl(self.parsed_path.query))
