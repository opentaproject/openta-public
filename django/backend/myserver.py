from wsgiref.simple_server import make_server
from django.core.handlers.wsgi import WSGIHandler
httpd = make_server('', 8000, WSGIHandler())
httpd.serve_forever()
