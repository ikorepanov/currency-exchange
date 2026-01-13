import json
from functools import cached_property
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import ParseResult, parse_qsl, unquote, urlparse

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
from currency_exchange.mvc_layers.service import Service
from currency_exchange.utils.string_helpers import serialize
from currency_exchange.utils.validation import is_valid_cur_code


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
            params = self.query_params
            from_lst = params.get('from')
            to_lst = params.get('to')
            amount_lst = params.get('amount')
            if from_lst is not None and to_lst is not None and amount_lst is not None:
                self.exchange(from_lst[0], to_lst[0], float(amount_lst[0]))
            else:
                self.send_error(
                    HTTPStatus.BAD_REQUEST, 'Не переданы один или несколько параметров'
                )

        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')

    def do_POST(self) -> None:
        if self.first_segment == 'currencies' and len(self.path_segments) == 1:
            params = self.request_params
            name_lst = params.get('name')
            code_lst = params.get('code')
            sign_lst = params.get('sign')
            if name_lst is not None and code_lst is not None and sign_lst is not None:
                self.create_currency(name_lst[0], code_lst[0], sign_lst[0])
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, 'Отсутствует нужное поле формы')

        elif self.first_segment == 'exchangeRates' and len(self.path_segments) == 1:
            params = self.request_params
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
        if self.first_segment == 'exchangeRate':
            if len(self.path_segments) == 1:
                self.send_error(HTTPStatus.BAD_REQUEST)
            elif len(self.path_segments) == 2:
                code_pair = self.second_segment

                params = self.request_params
                rate_lst = params.get('rate')
                if rate_lst is not None and code_pair is not None:
                    self.update_rate(code_pair, float(rate_lst[0]))

        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def get_currencies(self) -> None:
        if len(self.path_segments) == 1:
            try:
                data = self.service.get_currencies()
                response = serialize(data)
                self.send_json_response(HTTPStatus.OK, response)
            except NoDataBaseConnectionError as error:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')

    def get_currency(self) -> None:
        if self.second_segment is None:
            self.send_error(HTTPStatus.BAD_REQUEST, 'Код валюты отсутствует в адресе')
        elif len(self.path_segments) == 2:
            if is_valid_cur_code(self.second_segment):
                try:
                    data = self.service.get_currency(self.second_segment)
                    response = serialize(data)
                    self.send_json_response(HTTPStatus.OK, response)
                except NoDataBaseConnectionError as error:
                    self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
                except NoCurrencyError as error:
                    self.send_error(HTTPStatus.NOT_FOUND, str(error))
            else:
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    'Код валюты должен состоять из 3 заглавных английских букв',
                )
        else:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')

    def get_rates(self) -> None:
        if len(self.path_segments) > 1:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')
        try:
            data = self.service.get_all_rates()
            response = serialize(data)
            self.send_json_response(HTTPStatus.OK, response)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')

    def get_rate(self) -> None:
        if len(self.path_segments) > 2:
            self.send_error(HTTPStatus.NOT_FOUND, 'Ресурс не найден')
        if self.second_segment is None:
            self.send_error(
                HTTPStatus.BAD_REQUEST, 'Коды валют пары отсутствуют в адресе'
            )
        else:
            try:
                data = self.service.get_rate(self.second_segment)
                response = serialize(data)
                self.send_json_response(HTTPStatus.OK, response)
            except NoDataBaseConnectionError:
                self.send_error(
                    HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна'
                )
            except (NoCurrencyError, NoRateError):
                self.send_error(
                    HTTPStatus.NOT_FOUND, 'Обменный курс для пары не найден'
                )

    def create_currency(self, name: str, code: str, sign: str) -> None:
        try:
            response = serialize(
                self.service.save_currency(CurrencyPostDto(name, code, sign))
            )
            self.send_json_response(
                HTTPStatus.CREATED,
                response,
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
        try:
            response = serialize(
                self.service.save_rate(
                    RatePostUpdateDto(base_currency_code, target_currency_code, rate)
                )
            )
            self.send_json_response(
                HTTPStatus.CREATED,
                response,
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
        try:
            response = serialize(
                self.service.update_rate(
                    RatePostUpdateDto(code_pair[:3], code_pair[3:], rate)
                )
            )
            self.send_json_response(
                HTTPStatus.OK,
                response,
            )
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST)
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except NoCurrencyPairError:
            self.send_error(HTTPStatus.NOT_FOUND)

    def exchange(self, from_cur_code: str, to_cur_code: str, amount: float) -> None:
        try:
            response = serialize(
                self.service.exchange_currencies(
                    ExchangePostDto(from_cur_code, to_cur_code, amount)
                )
            )
            self.send_json_response(
                HTTPStatus.OK,
                response,
            )
        except NoDataBaseConnectionError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'База данных недоступна')
        except CantConvertError:
            self.send_error(HTTPStatus.NOT_FOUND)

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
