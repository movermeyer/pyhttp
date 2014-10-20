import json
import umsgpack
from pydic import Parameters
import re
import time
try:
    #python 2.x
    from urllib import quote_plus as url_encode
except ImportError:
    #python 3.x
    from urllib.parse import quote_plus as url_encode


class Request:
    def __init__(self, method, path=None,
                 query=None, data=None, cookies=None, files=None, headers=None,
                 host='', protocol='http', remote_ip=None, version=None):
        """
        @type method: str
        @type path: str or None
        @type query: dict or None
        @type data: dict or None
        @type cookies: dict or None
        @type files: list or None (a list with dicts that contains "content" and "name")
        @type headers: dict or None
        @type host: str
        @type protocol: str
        @type remote_ip: str or None
        @type version: str or None
        """
        self.path = path.strip('/') if path else None
        if not self.path:
            self.path = '/'

        self.method = method.upper()

        self.query = Parameters(query if query else {})
        self.data = Parameters(data if data else {})
        self.cookies = Parameters(cookies if cookies else {})
        self.files = files
        self.headers = Parameters(headers if headers else {})

        self.host = host
        self.protocol = protocol
        self.remote_ip = remote_ip
        self.version = version


class Response:
    # See http://www.iana.org/assignments/http-status-codes
    REASON_PHRASES = {
        100: 'Continue',
        101: 'Switching Protocols',
        102: 'Processing',  # RFC2518
        200: 'OK',
        201: 'Created',
        202: 'Accepted',
        203: 'Non-Authoritative Information',
        204: 'No Content',
        205: 'Reset Content',
        206: 'Partial Content',
        207: 'Multi-Status',  # RFC4918
        208: 'Already Reported',  # RFC5842
        226: 'IM Used', # RFC3229
        300: 'Multiple Choices',
        301: 'Moved Permanently',
        302: 'Found',
        303: 'See Other',
        304: 'Not Modified',
        305: 'Use Proxy',
        306: 'Reserved',
        307: 'Temporary Redirect',
        308: 'Permanent Redirect',  # RFC-reschke-http-status-308-07
        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Payment Required',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        407: 'Proxy Authentication Required',
        408: 'Request Timeout',
        409: 'Conflict',
        410: 'Gone',
        411: 'Length Required',
        412: 'Precondition Failed',
        413: 'Request Entity Too Large',
        414: 'Request-URI Too Long',
        415: 'Unsupported Media Type',
        416: 'Requested Range Not Satisfiable',
        417: 'Expectation Failed',
        418: 'I\'m a teapot',  # RFC2324
        422: 'Unprocessable Entity',  # RFC4918
        423: 'Locked',  # RFC4918
        424: 'Failed Dependency',  # RFC4918
        425: 'Reserved for WebDAV advanced collections expired proposal',  # RFC2817
        426: 'Upgrade Required',  # RFC2817
        428: 'Precondition Required',  # RFC6585
        429: 'Too Many Requests',  # RFC6585
        431: 'Request Header Fields Too Large',  # RFC6585
        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
        505: 'HTTP Version Not Supported',
        506: 'Variant Also Negotiates (Experimental)',  # RFC2295
        507: 'Insufficient Storage',  # RFC4918
        508: 'Loop Detected',  # RFC5842
        510: 'Not Extended',  # RFC2774
        511: 'Network Authentication Required',  # RFC6585
    }

    def __init__(self, data='', status_code=200, status_text=None, headers=None):
        self._status_code = status_code
        self._status_text = status_text
        self.data = data
        self.headers = headers if headers is not None else Parameters()

    def set_status(self, code=None, text=None):
        """
        @type code: int
        @type text: str
        """
        if code:
            if code < 100 or code > 599:
                raise Exception('Invalid status code: %i' % code)
            self._status_code = code
        self._status_text = text if text else self.REASON_PHRASES[code] if code in self.REASON_PHRASES else ''
        return self

    def get_status_code(self):
        return self._status_code

    def get_status_text(self):
        return self._status_text

    def get_content(self):
        return self.data


class JsonResponse(Response):
    def get_content(self):
        return json.dumps(self.data)


class MsgpackResponse(Response):
    def get_content(self):
        return umsgpack.packb(self.data)


class Cookie:
    def __init__(self, name, value, expire=0, path='/', domain=None, secure=False, http_only=True):
        """
        @type name: str         The name of the cookie
        @type value: str        The value of the cookie
        @type expire: int       The time the cookie expires
        @type path: str         The path on the server in which the cookie will be available on
        @type domain: str       The domain that the cookie is available to
        @type secure: bool      Whether the cookie should only be transmitted over a secure HTTPS connection from the client
        @type http_only: bool   Whether the cookie will be made accessible only through the HTTP protocol

        """
        if not name:
            raise CookieException('The cookie name cannot be empty.')

        if re.match(r"[=,; \t\r\n\013\014]", name):
            raise CookieException('The cookie name "%s" contains invalid characters.' % name)

        if not isinstance(expire, int) or expire < 0:
            raise CookieException('The cookie expiration time is not valid.')

        self._name = name
        self._value = value
        self._domain = domain
        self._expire = expire
        self._path = path
        self._secure = secure
        self._http_only = http_only

    def get_name(self):
        return self._name

    def get_value(self):
        return self._value

    def get_domain(self):
        return self._domain

    def get_expires_time(self):
        return self._expire

    def get_path(self):
        return self._path

    def is_secure(self):
        return self._secure

    def is_http_only(self):
        return self._http_only

    def is_cleared(self):
        return self._expire < int(round(time.time()))

    def __str__(self):
        string = '%s=' % url_encode(self.get_name())

        if self._value == '':
            string = '%sdeleted; expires=Thu, 01-Jan-1970 00:00:00 GMT' % string
        else:
            string = '%s%s' % (string, url_encode(self._value))

            if self._expire != 0:
                string = '%s; expires=%s' % (string, time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(self._expire)))

        if self._path:
            string = '%s; path=%s' % (string, self._path)

        if self._domain:
            string = '%s; domain=%s' % (string, self._domain)

        if self._secure:
            string = '%s; secure' % string

        if self._http_only:
            string = '%s; httponly' % string

        return string


class CookieException(Exception):
    pass
