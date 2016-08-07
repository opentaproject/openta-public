from wsgiref.simple_server import make_server
from waitress import serve
from pyramid.config import Configurator
from pyramid.response import Response, FileResponse
from pyramid.request import Request
from pyramid.view import view_config
from pyramid.events import NewRequest
from pyramid.httpexceptions import HTTPNotFound
from xml.etree.ElementTree import fromstring
from symbolic_server import Symbolic
from response import (
    exercisesResponse,
    exerciseJSONResponse,
    exerciseXMLResponse,
    exerciseAssetResponse,
    exerciseCheckResponse,
)

from json import dumps
import os


def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update(
            {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
                'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Max-Age': '1728000',
            }
        )

    event.request.add_response_callback(cors_headers)


def hello_world(request):
    return Response('Hello %(name)s!' % request.matchdict)


if __name__ == '__main__':
    config = Configurator()

    config.add_route('exercisejson', '/exercise/{name}')
    config.add_route('exercisexml', '/exercise/{name}/xml')
    config.add_route('exercises', '/exercises')
    config.add_route('exerciseasset', '/exercise/{name}/asset/{asset}')
    config.add_route('exercisecheck', '/exercise/{name}/question/{num}/check')

    config.add_view(exercisesResponse, route_name='exercises', renderer='json')
    config.add_view(exerciseJSONResponse, route_name='exercisejson', renderer='json')
    config.add_view(exerciseXMLResponse, route_name='exercisexml', renderer='string')
    config.add_view(exerciseAssetResponse, route_name='exerciseasset')
    config.add_view(exerciseCheckResponse, route_name='exercisecheck', renderer='json')

    config.add_subscriber(add_cors_headers_response_callback, NewRequest)
    app = config.make_wsgi_app()
    serve(app, port=8000)
