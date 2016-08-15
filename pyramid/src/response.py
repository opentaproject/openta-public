from pyramid.response import Response, FileResponse
from pyramid.httpexceptions import HTTPNotFound
from exercises import exercises, exerciseJSON, exerciseXML, exerciseCheck, exerciseSave
import os


def exercisesResponse(request):  # {{{
    exerciselist = exercises()
    print(exerciselist)
    return exerciselist  # }}}


# Need to split into JSON reading part and request handling
def exerciseJSONResponse(request):  # {{{
    obj = exerciseJSON(request.matchdict['name'])
    return obj  # }}}


def exerciseXMLResponse(request):  # {{{
    xml = exerciseXML(request.matchdict['name'])
    return xml  # }}}


def exerciseAssetResponse(request):  # {{{
    file = './exercises/{name}/{asset}'.format(**request.matchdict)
    if os.path.isfile(file):
        return FileResponse(file, request=request)
    else:
        return HTTPNotFound('Asset does not exist.')  # }}}


def exerciseCheckResponse(request):  # {{{
    result = exerciseCheck(
        request.matchdict['name'], int(request.matchdict['num']), request.json_body['expression']
    )
    print(result)
    return result  # }}}


def exerciseSaveResponse(request):
    result = {}
    try:
        result = exerciseSave(request.matchdict['name'], request.json_body['xml'])
    except IOError:
        result = {'success': False}
    return result
