# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import os
import re
import urllib.parse


from django.conf import settings
from django.http import FileResponse, HttpResponse

logger = logging.getLogger(__name__)

# FIXME this needs a complete rewrite using pytest


def serve_file(path, filename, **kwargs):
    devpath = ''
    if "dev_path" in kwargs:
        devpath = kwargs["dev_path"]
        dev_path = devpath
    else :
        devpath = kwargs["devpath"]
        dev_path = devpath

    xpath = ''
    if "accel_xpath" in kwargs:
        xpath = urllib.parse.quote(kwargs["accel_xpath"].encode("utf-8"))

    if  devpath and not os.path.exists( devpath ) :
        logger.error(f"==========> {devpath} file not found ; will try to fix")
        logger.error(f"SERVE_FILE KWARGS = {kwargs}")
        p = devpath.split('/');
        logger.error (f"exercise_key={p[4]}")
        path =  ('/').join(p[0:4])
        if os.path.exists( path ):
            hdir  = os.listdir( ('/').join(p[0:4]) )[0]
            logger.error(f"hdir = {hdir}")
            devpath = re.sub(p[4],hdir,devpath)
            xpath = re.sub(p[4], hdir, xpath)
            logger.error(f"XPATH = {xpath} DEVPATH={devpath}")

    
    source = kwargs['source']
    use_xpath = settings.USE_ACCEL_REDIRECT
    use_xpath =  use_xpath and ( not settings.RUNTESTS) and not "answer_image_view" in kwargs["source"] and not 'get_task_result_file' in kwargs['source'] 
    use_xpath = use_xpath and ( 'exercise_asset'  in source and 'thumbnail' in path )

    if  (use_xpath ):
        xpath = urllib.parse.quote(kwargs["accel_xpath"].encode("utf-8"))
        #
        # DON't USE ACCEL_REDIRECT WHEN HANDLING IMAGE VIEWING SINCE IMAGE EDITS
        # ARE NOT UPDATED. THESE ARE UNUSUAL OPERATIONS ANYWAY AND DON'T NEED REDIRECT
        #
        response = HttpResponse()
        content_type = kwargs["content_type"] if "content_type" in kwargs else None
        response["Content-Type"] = content_type if content_type else ""
        response["Content-Disposition"] = "inline; filename={0}".format(filename)
        response["X-Accel-Redirect"] = xpath
        return response
    else:
        content_type = kwargs["content_type"] if "content_type" in kwargs else None
        if content_type:
            ftype = devpath.split(".")[-1]
            if content_type == "image":
                content_type = f"{content_type}/{ftype}"
            try:
                f = open(devpath, "rb")
            except FileNotFoundError as e:
                logger.error(f"==========> {devpath} file still not found")
                return FileResponse()
            except Exception as e:
                logger.error(f"ERROR: FILE_HANDLING 2317 Exception = {type(e).__name__} file={devpath} ")
                return FileResponse()
            response = FileResponse(f, content_type)
            if not 'thumbnail' in filename :
                response["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"
            else :
                response['Cache-Control'] = 'max-age=120'
            # response['Content-Disposition'] = u'inline; filename="{}"'.format(filename)
            return response
        else:
            response = FileResponse(open(devpath, "rb"))
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            # response['Content-Disposition'] = u'inline; filename="{}"'.format(filename)
            return response


