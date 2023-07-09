#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from optparse import OptionParser
from http.server import BaseHTTPRequestHandler, HTTPServer

from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field:
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if self.required and value is None:
            raise ValueError('Missed required field')
        if self.nullable and value is None:
            raise ValueError("Field can't be nullable")


class CharField(Field):
    field_type = str

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, self.field_type):
            raise ValueError(f'Wrong value type. {self.field_type} expected,  got {type(value)}')


class ArgumentsField(Field):
    field_type = dict

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, self.field_type):
            raise ValueError(f'Wrong value type. {self.field_type} expected,  got {type(value)}')


class EmailField(CharField):
    def validate(self, value):
        super().validate(value)
        if value and '@' not in value:
            raise ValueError('Wrong email format')


class PhoneField(Field):
    field_type = str, int

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, self.field_type):
            raise ValueError(f'Wrong value type. {self.field_type} expected,  got {type(value)}')
        value_str = str(value)
        if len(value_str) != 11 or not value_str.startswith('7'):
            raise ValueError('Wrong phone number format')
        if value:
            try:
                int(value)
            except ValueError:
                raise ValueError('Wrong phone number format. Only digests are allowed.')


class DateField(CharField):
    date_format = '%d.%m.%Y'

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, self.field_type):
            raise ValueError(f'Wrong value type. {self.field_type} expected,  got {type(value)}')
        if value:
            try:
                datetime.strptime(value, self.date_format)
            except ValueError:
                raise ValueError('Wrong date format. DD.MM.YYYY expected')


class BirthDayField(DateField):
    years_limit = 70

    def validate(self, value):
        super().validate(value)
        if value:
            if (datetime.now() - datetime.strptime(value, self.date_format)) > timedelta(days=365.2 * self.years_limit):
                raise ValueError(f'Age should be less than {self.years_limit} years')


class GenderField(Field):
    field_type = int

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, self.field_type):
            raise ValueError(f'Wrong value type. {self.field_type} expected,  got {type(value)}')
        if value:
            if value not in GENDERS:
                raise ValueError(f'Gender must be an integer within  {list(GENDERS.keys())}')


class ClientIDsField(Field):
    field_type = list

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, self.field_type):
            raise ValueError(f'Wrong value type. {self.field_type} expected,  got {type(value)}')
        for client_id in value:
            if not isinstance(client_id, int):
                raise ValueError('Client ID must be an integer')


class RequestMeta(type):

    def __new__(cls, name, bases, attrs):
        fields = []
        for key, value in attrs.items():
            if isinstance(value, Field):
                value.name = key
                fields.append(value)
        new_cls = super(RequestMeta, cls).__new__(cls, name, bases, attrs)
        # new_cls = super().__new__(cls)
        new_cls.fields = fields
        return new_cls


class Request(metaclass=RequestMeta):
    context = {}
    
    def __init__(self, request):
        self.request = request
        self.errors = []

    def validate(self):
        if not isinstance(self.request, dict):
            self.errors.append(ERRORS[INVALID_REQUEST])
            return False
        for field in self.fields:
            value = self.request.get(field.name)
            if field.required and field.name not in self.request.keys():
                self.errors.append(f'{ERRORS[INVALID_REQUEST]}: {field.name} is not in a query')
            elif field.required and not field.nullable and not value:
                self.errors.append(f'{ERRORS[INVALID_REQUEST]}: {field.name} is null')
            elif not field.required and not value:
                setattr(self, field.name, '')
            else:
                try:
                    field.validate(value)
                    setattr(self, field.name, value)
                except Exception as e:
                    self.errors.append(f'{ERRORS[INVALID_REQUEST]}: {e}')

    def is_valid(self):
        return not self.errors


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def fill_context(self, ctx):
        self.context['nclients'] = ctx['nclients']

    def response(self, store):
        resp = {}
        for cid in self.client_ids:
            resp[cid] = get_interests(store, cid)
        return resp


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)
    _acceptable_pairs = [
        ['phone', 'email'],
        ['first_name', 'last_name'],
        ['gender', 'birthday'],
    ]

    def fill_context(self, ctx):
        self.context['has'] = ctx['has']
        self.context['is_admin'] = ctx['is_admin']

    def validate(self):
        fields = self.context.get('has', [])
        super().validate()
        is_valid = super().is_valid()
        if any([set(fields).issuperset(set(pair)) for pair in self._acceptable_pairs]):
            return is_valid and True
        else:
            self.errors.append(ERRORS[INVALID_REQUEST])
            return False

    def response(self, store):
        data = {
            'phone': self.phone,
            'email': self.email,
            'birthday': self.birthday,
            'gender': self.gender,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }
        if self.context['is_admin']:
            score = int(ADMIN_SALT)
        else:
            score = get_score(store, **data)
        return {'score': score}


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    handlers = {
        "online_score": OnlineScoreRequest,
        "clients_interests": ClientsInterestsRequest,
    }
    method_request = MethodRequest(request['body'])
    method_request.validate()
    if not method_request.is_valid():
        error = ', '.join(method_request.errors)
        logging.error(error)
        return error, INVALID_REQUEST
    if not check_auth(method_request):
        logging.error(ERRORS[FORBIDDEN])
        return ERRORS[FORBIDDEN], FORBIDDEN
    if method_request.method not in handlers:
        logging.error(ERRORS[INVALID_REQUEST])
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST

    if method_request.method == 'online_score':
        ctx['is_admin'] = method_request.is_admin
        ctx['has'] = [k for k, v in method_request.arguments.items() if v is not None]
    elif method_request.method == 'clients_interests':
        ctx['nclients'] = len(method_request.arguments.get('client_ids', []))
    request_data = handlers[method_request.method](method_request.arguments)
    request_data.fill_context(ctx)
    request_data.validate()
    if request_data.errors or not request_data.is_valid():
        error = ', '.join(request_data.errors)
        logging.error(error)
        return error, INVALID_REQUEST
    response = request_data.response(store)
    logging.info("Success request")
    return response, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except Exception as e:
            logging.error(e)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
