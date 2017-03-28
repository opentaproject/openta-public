import backend.settings as settings
from django.http import FileResponse, HttpResponse, StreamingHttpResponse


def serve_file(path, filename, **kwargs):  # {{{
    content_type = kwargs['content_type'] if 'content_type' in kwargs else None
    dev_path = kwargs['dev_path'] if 'dev_path' in kwargs else path

    if settings.RUNNING_DEVSERVER:
        if content_type:
            return FileResponse(open(dev_path, 'rb'), content_type)
        else:
            return FileResponse(open(dev_path, 'rb'))
    else:
        response = HttpResponse()
        response["Content-Type"] = content_type if content_type else ""
        response["Content-Disposition"] = "inline; filename={0}".format(filename)
        response["X-Accel-Redirect"] = path.encode('utf-8')
        return response  # }}}
