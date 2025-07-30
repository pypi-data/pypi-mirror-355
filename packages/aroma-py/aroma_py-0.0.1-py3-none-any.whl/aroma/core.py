import http.server
import socketserver
import re
import urllib.parse
import json
import time
import os
import mimetypes
from http import cookies
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

class Request:
    def __init__(self, handler):
        self.handler = handler
        self.method = handler.command
        self.path = urllib.parse.urlparse(handler.path).path
        self.query = urllib.parse.parse_qs(urllib.parse.urlparse(handler.path).query)
        self.headers = handler.headers
        self.cookies = cookies.SimpleCookie(handler.headers.get('Cookie'))
        self.body = None
        self.params = {}
        self.session = {}

    def json(self):
        length = int(self.handler.headers.get('Content-Length', 0))
        body = self.handler.rfile.read(length)
        return json.loads(body.decode('utf-8')) if body else {}

    def form(self):
        length = int(self.handler.headers.get('Content-Length', 0))
        body = self.handler.rfile.read(length)
        return urllib.parse.parse_qs(body.decode('utf-8')) if body else {}


class Response:
    def __init__(self, handler):
        self.handler = handler
        self.status_code = 200
        self.headers = {'X-Powered-By': 'Aroma.py/0.1'}
        self._cookies = cookies.SimpleCookie()

    def set_header(self, key, value):
        self.headers[key] = value

    def set_cookie(self, key, value, **options):
        self._cookies[key] = value
        for opt, val in options.items():
            self._cookies[key][opt] = val

    def status(self, code):
        self.status_code = code
        return self

    def send(self, data):
        if isinstance(data, dict):
            self.headers['Content-Type'] = 'application/json'
            body = json.dumps(data).encode('utf-8')
        else:
            body = data.encode('utf-8') if isinstance(data, str) else data

        self.handler.send_response(self.status_code)
        for k, v in self.headers.items():
            self.handler.send_header(k, v)
        for morsel in self._cookies.values():
            self.handler.send_header('Set-Cookie', morsel.OutputString())
        self.handler.end_headers()
        self.handler.wfile.write(body)

    def json(self, data):
        self.set_header('Content-Type', 'application/json')
        self.send(json.dumps(data))

    def render(self, template_name, data, env):
        template = env.get_template(template_name)
        html = template.render(**data)
        self.set_header('Content-Type', 'text/html')
        self.send(html)


class Router:
    def __init__(self):
        self.routes = []
        self.middlewares = []

    def use(self, fn):
        self.middlewares.append(fn)

    def route(self, method, path, handler):
        param_names = re.findall(r':(\w+)', path)
        pattern = re.sub(r':\w+', r'([^/]+)', path)
        pattern = f'^{pattern}$'
        self.routes.append((method, re.compile(pattern), handler, param_names, path))

    def get(self, path, handler):
        self.route('GET', path, handler)

    def post(self, path, handler):
        self.route('POST', path, handler)

    def put(self, path, handler):
        self.route('PUT', path, handler)

    def delete(self, path, handler):
        self.route('DELETE', path, handler)

    def match(self, method, path):
        for m, pattern, handler, param_names, _ in self.routes:
            if m == method:
                match = pattern.match(path)
                if match:
                    params = dict(zip(param_names, match.groups()))
                    return handler, params
        return None, {}


class Aroma:
    def __init__(self):
        self.router = Router()
        self.middlewares = []
        self.static_path = None
        self.error_handler = None
        self.metrics_enabled = False
        self.request_count = 0
        self.sessions = defaultdict(dict)
        self.env = Environment(loader=FileSystemLoader('views'))

    def use(self, fn):
        self.middlewares.append(fn)

    def get(self, path, handler):
        self.router.get(path, handler)

    def post(self, path, handler):
        self.router.post(path, handler)

    def put(self, path, handler):
        self.router.put(path, handler)

    def delete(self, path, handler):
        self.router.delete(path, handler)

    def serve_static(self, path):
        self.static_path = path

    def handle_errors(self, fn):
        self.error_handler = fn

    def metrics(self, path='/metrics'):
        self.metrics_enabled = True
        def handler(req, res):
            res.json({
                'status': 'ok',
                'uptime': time.time() - START_TIME,
                'requests': self.request_count,
                'timestamp': time.ctime()
            })
        self.get(path, handler)

    def use_router(self, prefix, router):
        for method, _, handler, _, original_path in router.routes:
            full_path = f"{prefix.rstrip('/')}/{original_path.lstrip('/')}"
            self.router.route(method, full_path, handler)

    def listen(self, port):
        app = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_HEAD(self): self.do_GET()
            def do_GET(self): self._handle()
            def do_POST(self): self._handle()
            def do_PUT(self): self._handle()
            def do_DELETE(self): self._handle()

            def _handle(self):
                app.request_count += 1
                req = Request(self)
                res = Response(self)

                sid = req.cookies.get('sid')
                if sid:
                    sid = sid.value
                else:
                    sid = str(time.time()) + str(len(app.sessions))
                    res.set_cookie('sid', sid)

                req.session = app.sessions[sid]

                for mw in app.middlewares:
                    mw(req, res)

                if app.static_path and req.path.startswith('/static/'):
                    file_path = os.path.join(app.static_path, req.path.replace('/static/', '', 1))
                    if os.path.exists(file_path):
                        res.set_header('Content-Type', mimetypes.guess_type(file_path)[0] or 'text/plain')
                        with open(file_path, 'rb') as f:
                            res.send(f.read())
                        return

                handler, params = app.router.match(req.method, req.path)
                if handler:
                    req.params = params
                    try:
                        handler(req, res)
                    except Exception as e:
                        if app.error_handler:
                            app.error_handler(e, req, res)
                        else:
                            res.status(500).send('Internal Server Error')
                else:
                    res.status(404).send('404 Not Found')

        try:
            with socketserver.TCPServer(('127.0.0.1', port), Handler) as httpd:
                print(f"Aroma.py server running at http://127.0.0.1:{port}")
                httpd.serve_forever()
        except OSError as e:
            if e.errno == 138:
                print("Environment does not support socket binding (Errno 138).")
            else:
                raise


START_TIME = time.time()
