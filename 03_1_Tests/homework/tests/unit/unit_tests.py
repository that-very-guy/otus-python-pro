import unittest
import functools

from scoring_api import api, store


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestFields(unittest.TestCase):
    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    @cases([
        (True, True, None),
    ])
    def test_basic_field(self, required, nullable, value):
        field = api.Field(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, 123),
        (False, False, [1, 2]),
        (False, True, None),
    ])
    def test_char_field(self, required, nullable, value):
        field = api.CharField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, 123),
        (False, False, '123'),
        (False, False, None),
    ])
    def test_arguments_field(self, required, nullable, value):
        field = api.ArgumentsField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, 'foo.gmail.com'),
        (False, False, 123),
    ])
    def test_email_field(self, required, nullable, value):
        field = api.EmailField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, 7999),
        (False, False, '7999'),
        (False, False, '89990123456'),
        (False, False, '+79990123456'),
    ])
    def test_phone_field(self, required, nullable, value):
        field = api.PhoneField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, 20000101),
        (False, False, '01-01-2000'),
        (False, False, '01/01/2000'),
        (False, False, 'foo-bar'),
    ])
    def test_date_field(self, required, nullable, value):
        field = api.DateField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, '01-01-2000'),
        (False, False, '01.01.1900'),
    ])
    def test_birthday_field(self, required, nullable, value):
        field = api.BirthDayField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (False, False, 123),
        (False, False, '1'),
        (False, False, -999),
    ])
    def test_gender_field(self, required, nullable, value):
        field = api.GenderField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)

    @cases([
        (True, True, 123),
        (True, True, '123'),
        (True, True, ['123', '321']),
        (True, True, []),
        (True, True, None),
    ])
    def test_client_ids_field(self, required, nullable, value):
        field = api.ClientIDsField(required, nullable)
        with self.assertRaises(ValueError):
            field.validate(value)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.storage = store.DBConnector()

    def cache_set(self):
        self.assertEqual(self.storage.cache_get('key_does_not_exist'), None)
        self.assertEqual(self.storage.cache_set('key_does_not_exist', 'foo', 10), 'foo')

    def test_cache_get(self):
        self.assertEqual(self.storage.cache_get('key_does_not_exist'), None)

    def test_get(self):
        self.assertEqual(self.storage.get('key_does_not_exist'), None)


if __name__ == "__main__":
    unittest.main()
