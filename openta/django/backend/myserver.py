# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from wsgiref.simple_server import make_server
from django.core.handlers.wsgi import WSGIHandler

httpd = make_server("", 8000, WSGIHandler())
httpd.serve_forever()
