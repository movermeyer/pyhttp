from unittest import TestCase
from pyhttp import Request, Response, JsonResponse, MsgpackResponse, Cookie, CookieException
import time


class RequestTestCase(TestCase):
    def test_instance(self):
        request = Request('GET', 'foo/bar', {'hello': 'world', 'aaa': 111}, {'bbb': 222, 'ccc': 333})
        self.assertEqual(request.path, 'foo/bar')
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.query.all(), {'hello': 'world', 'aaa': 111})
        self.assertEqual(request.data.all(), {'bbb': 222, 'ccc': 333})

    def test_trim_path(self):
        request = Request('GET', '/foo/bar')
        self.assertEqual(request.path, 'foo/bar')
        request = Request('GET', '/foo/bar/')
        self.assertEqual(request.path, 'foo/bar')
        request = Request('GET', 'foo/bar/')
        self.assertEqual(request.path, 'foo/bar')
        request = Request('GET', 'foo/bar')
        self.assertEqual(request.path, 'foo/bar')

    def test_upper_method(self):
        request = Request('POST')
        self.assertEqual(request.method, 'POST')
        request = Request('post')
        self.assertEqual(request.method, 'POST')
        request = Request('PoSt')
        self.assertEqual(request.method, 'POST')


class ResponseTestCase(TestCase):
    def test_default(self):
        response = Response()
        self.assertEqual(response.get_status_code(), 200)
        self.assertEqual(response.get_status_text(), None)
        self.assertEqual(response.data, '')

    def test_status(self):
        response = Response()

        response.set_status(404)
        self.assertEqual(response.get_status_code(), 404)
        self.assertEqual(response.get_status_text(), 'Not Found')

        response.set_status(500)
        self.assertEqual(response.get_status_code(), 500)
        self.assertEqual(response.get_status_text(), 'Internal Server Error')

        response.set_status(307, 'Custom message')
        self.assertEqual(response.get_status_code(), 307)
        self.assertEqual(response.get_status_text(), 'Custom message')

        response.set_status(500)
        response.set_status(text='Hello World')
        self.assertEqual(response.get_status_code(), 500)
        self.assertEqual(response.get_status_text(), 'Hello World')

        response.set_status(599)
        self.assertEqual(response.get_status_code(), 599)
        self.assertEqual(response.get_status_text(), '')

        self.assertRaises(Exception, response.set_status, 601)

        self.assertRaises(Exception, response.set_status, 99)

    def test_get_content(self):
        response = Response()

        response.data = 'FOO'
        self.assertEqual('FOO', response.get_content())


class JsonResponseTestCase(TestCase):
    def test_content(self):
        response = JsonResponse()

        response.data = {'foo': 'bar'}
        self.assertEqual(response.get_content(), '{"foo": "bar"}')

        response.data = None
        self.assertEqual(response.get_content(), 'null')

        response.data = ''
        self.assertEqual(response.get_content(), '""')


class MsgpackResponseTestCase(TestCase):
    def test_content(self):
        response = MsgpackResponse()
        response.data = {5: True, 2: 0}

        self.assertEqual(response.get_content(), b'\x82\x02\x00\x05\xc3')


class CookiesTestCase(TestCase):
    def test_instantiation_throws_exception_if_cookie_name_contains_invalid_characters(self):
        invalid_names = [
            '',
            ',MyName',
            ';MyName',
            ' MyName',
            '\tMyName',
            '\rMyName',
            '\nMyName',
            '\013MyName',
            '\014MyName'
        ]
        for invalid_name in invalid_names:
            self.assertRaises(CookieException, Cookie, *(invalid_name, 'bar'))

    def test_invalid_expiration(self):
        self.assertRaises(CookieException, Cookie, *('MyCookie', 'foo', 'bar'))

    def test_get_value(self):
        value = 'MyValue'
        cookie = Cookie('MyCookie', value)

        self.assertEqual(value, cookie.get_value())

    def test_get_path(self):
        cookie = Cookie('foo', 'bar')

        self.assertEqual('/', cookie.get_path())

    def test_get_expires_time(self):
        cookie = Cookie('foo', 'bar', 3600)

        self.assertEqual(3600, cookie.get_expires_time())

    def test_get_domain(self):
        cookie = Cookie('foo', 'bar', 3600, '/', 'example.com')

        self.assertEqual('example.com', cookie.get_domain())

    def test_is_secure(self):
        cookie = Cookie('foo', 'bar', 3600, '/', 'example.com', True)

        self.assertTrue(cookie.is_secure())

    def test_is_http_only(self):
        cookie = Cookie('foo', 'bar', 3600, '/', 'example.com', False, True)

        self.assertTrue(cookie.is_http_only())

    def test_cookie_is_not_cleared(self):
        cookie = Cookie('foo', 'bar', int(round(time.time()))+3600*24)

        self.assertFalse(cookie.is_cleared())

    def test_cookie_is_cleared(self):
        cookie = Cookie('foo', 'bar', int(round(time.time()))-20)

        self.assertTrue(cookie.is_cleared())

    def test_to_string(self):
        cookie = Cookie('foo', 'bar', 1, '/', 'example.com', True)
        self.assertEquals('foo=bar; expires=Thu, 01-Jan-1970 00:00:01 GMT; path=/; domain=example.com; secure; httponly', str(cookie))

        cookie = Cookie('foo', '', 1, '/admin/', 'example.com')
        self.assertEqual('foo=deleted; expires=Thu, 01-Jan-1970 00:00:00 GMT; path=/admin/; domain=example.com; httponly', str(cookie))

        cookie = Cookie('foo', 'bar', 0, '/', '')
        self.assertEqual('foo=bar; path=/; httponly', str(cookie))
