# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander
from django.contrib import messages

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
from twilio.rest import Client
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
import json
import logging
from utils import get_subdomain, get_subdomain_and_db , get_subdomain_and_db_and_user
from django.core.mail import EmailMessage
from utils import  send_email_object
from .send_sms import send_sms

import os
from twilio.rest import Client
#TWILIO_SID = os.environ.get('TWILIO_SID', None)
#TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', None)
#TWILIO_TO = os.environ.get('TWILIO_TO',None)
#TWILIO_FROM = os.environ.get("TWILIO_FROM",None)
#BUG_TO_EMAIL = os.environ.get("BUG_TO_EMAIL",None)
#BUG_FROM_EMAIL = os.environ.get("BUG_FROM_EMAIL",None) 
#BUG_CC_EMAIL = os.environ.get("BUG_CC_EMAIL",None) 
from django.contrib.auth import logout as syslogout


def truncate_words(s: str, limit: int = 55) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    cut = s.rfind(" ", 0, limit + 1)  # last space at/before limit
    if cut == -1:                      # no space → hard cut
        return s[:limit].rstrip()
    return s[:cut].rstrip()
#
#def send_sms( subject, body ):
#    do_sms = TWILIO_TO and TWILIO_FROM and TWILIO_SID and TWILIO_TOKEN
#    sms_body = truncate_words(subject)
#    if do_sms :
#        client = Client(TWILIO_SID, TWILIO_TOKEN)
#        message = client.messages.create(
#            to=TWILIO_TO,        # Recipient (Swedish number, E.164 format)
#            from_=TWILIO_FROM,     # Your Twilio number (SMS-capable)
#            body=sms_body
#          )
#    else :
#        logger.error(f"TWILIO NOT CONFIGGURE MESSAGE {sms_body} WAS NOT SENT BY SMS")
#    print(f"MESSAGE SENT {message.sid}")
#    return message.sid

logger = logging.getLogger('bugreport')
@require_POST
@csrf_protect
def bug_report(request):
    print(f"BUG_REPORT {request.POST}")
    subdomain, db = get_subdomain_and_db( request )
    failed = False
    try:
        user = request.user
        is_authenticated = getattr(request.user, 'is_authenticated', False)
        failed = not is_authenticated
    except Exception as err:
        logger.error("REQUEST USER IS NOT AUTHENTICATED FOR SMS")
        failed = True
        is_authenticated = False
    logger.error(f"SMS FAILED = {failed}")
    if failed:
        messages.add_message(request, messages.WARNING, "Not enrolled!")
        messages.error(request, "Message failed.")
        syslogout(request)
        if not is_authenticated :
            return JsonResponse({'ok': False,  'error': 'Message was not sent; You need to be logged in'}, status=403)
        else :
            return JsonResponse({'ok': False,  'error': 'Message could not be sent. '}, status=403)
    try:
        if request.META.get('CONTENT_TYPE', '').startswith('application/json'):
            payload = json.loads(request.body.decode('utf-8') or '{}')
        else:
            payload = request.POST.dict()
        message = (payload.get('message') or '').strip()
        page_url = payload.get('url') or request.META.get('HTTP_REFERER', '')
        user_agent = payload.get('userAgent') or request.META.get('HTTP_USER_AGENT', '')
        user = request.user 
        username = user.username
        subject = f"Bugreport {subdomain}.{settings.OPENTA_SERVER}:{username}   " + (payload.get('subject') or '').strip()
        if not message:
            return JsonResponse({'ok': False, 'error': 'message is required'}, status=400)
        logger.warning(
            "Bug report by %s: %s | url=%s ua=%s",
            getattr(user, 'username', 'anonymous'), message, page_url, user_agent
        )
        to_email = settings.BUG_TO_EMAIL
        to = [to_email] 
        reply_to = [to_email]
        cc = [ settings.BUG_CC_EMAIL ]
        try :
            user_email = user.email
            if user_email :
                cc.append(user_email)
        except :
            pass
        from_email = settings.BUG_FROM_EMAIL
        print(f"FROM_EMAIL = {from_email}")
        message = f"{username} at {subdomain}\n{message}"
        #print(f"MESSAGE = {message}")
        #print(f"SUBJECT = {subject}")
        #print(f"FROM = {from_email}")
        #print(f"CC = {cc}")
        #print(f"TO = {to}")
        #print(f"REPLY_TO = {reply_to}")
        #print(f"TWILIO_FROM = {settings.TWILIO_FROM}")
        body = message
        body = body + "\nYou can follow up on the bug report by doing a Reply to all and include whatever more information is necessary. \nFeedback on your request will come via this thread as well\nPlease do not change the subject line when replying."
        sms_body = subject  + ": " + message
        logger.error(f"SMS_BODY = {sms_body}")
        if not settings.RUNNING_DEVSERVER  and not settings.RUNTESTS :
            msg = send_sms( sms_body )
            logger.error(f"SMS_OBJECT_SENT MSG = {msg}")
        else :
            logger.error(f"RUNNING LODCAL AND MESSAGE NOT SENT")
        email_object = EmailMessage( subject=subject, body=body , from_email=from_email, to=to , reply_to=reply_to, cc=cc)
        #print(f"EMAIL_OBJECT = {email_object}")
        res = email_object.send()
        logger.error(f"EMAIL_OBJECT_SENT RES = {res}")
        do_sms = settings.TWILIO_TO and settings.TWILIO_FROM and settings.TWILIO_SID and settings.TWILIO_TOKEN
        sms_body = truncate_words(subject)
        if do_sms :
            client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
            message = client.messages.create(
                to=settings.TWILIO_TO,        # Recipient (Swedish number, E.164 format)
                from_=settings.TWILIO_FROM,     # Your Twilio number (SMS-capable)
                body=sms_body
                )
        else :
            logger.error(f"settings.TWILIO NOT CONFIGGURE MESSAGE {message} WAS NOT SENT BY SMS")
        return JsonResponse({'ok': True})



    except Exception as e:
        logger.error(f"ERROR IN BUG {str(e)}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
