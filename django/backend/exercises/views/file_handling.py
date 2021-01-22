import logging
from django.conf import settings
from django.http import FileResponse, HttpResponse

logger = logging.getLogger(__name__)


def serve_file(path, filename, **kwargs):
    content_type = kwargs['content_type'] if 'content_type' in kwargs else None
    dev_path = kwargs['dev_path'] if 'dev_path' in kwargs else "./" + path
    logger.info("SERVE_FILE FILENAME = " +  filename )
    logger.info("PATH FOR X-Accel-Rediret = " +  path )
    if settings.RUNNING_DEVSERVER:
        logger.info("FILE_HANDLING  DEVSERVER ")
        if content_type:
            response = FileResponse(open(dev_path, 'rb'), content_type)
            response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
            return response
        else:
            response = FileResponse(open(dev_path, 'rb'))
            response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
            return response
    else:
        logger.info("INLINE FILENAME " + filename )
        logger.info("PATH = " + str(  path ) )
        response = HttpResponse()
        response["Content-Type"] = content_type if content_type else ""
        response["Content-Disposition"] = "inline; filename={0}".format(filename)
        response["X-Accel-Redirect"] = path.encode('utf-8')
        return response
