# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
from django.conf import settings
import logging
from twilio.rest import Client

logger = logging.getLogger('bugreport')


def truncate_words(s: str, limit: int = 55) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    cut = s.rfind(" ", 0, limit + 1)  # last space at/before limit
    if cut == -1:                      # no space → hard cut
        return s[:limit].rstrip()
    return s[:cut].rstrip()




# --- Your Twilio credentials (from https://console.twilio.com/) ---

def send_sms( sms_body ):
    logger.error(f"SEND_SMS_BODY {sms_body}")
    do_sms = settings.TWILIO_TO and settings.TWILIO_FROM and settings.TWILIO_SID and settings.TWILIO_TOKEN
    logger.error(f"DO_SMS {do_sms}")
    sms_body = truncate_words(sms_body, 120 )
    logger.error(f"BODY = {sms_body}")
    logger.error(f"TWILIO_TO = {settings.TWILIO_TO}")
    logger.error(f"TWILIO_FROM = {settings.TWILIO_FROM}")
    logger.error(f"TWILIO_SID = {settings.TWILIO_SID}")
    logger.error(f"TWILIO_TOKEN = {settings.TWILIO_TOKEN}")
    if do_sms :
        client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        message = client.messages.create(
            to=settings.TWILIO_TO,        # Recipient (Swedish number, E.164 format)
            from_=settings.TWILIO_FROM,     # Your Twilio number (SMS-capable)
            body=sms_body
          )
        logger.error(f"MESSAGE SENT {message.sid}")
        return message.sid
    else :
        logger.error(f"TWILIO NOT CONFIGURE MESSAGE {sms_body} WAS NOT SENT BY SMS")



# --- Initialize client ---
if False and account_sid and auth_token :
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        to=settings.TWILIO_TO,        # Recipient (Swedish number, E.164 format)
        from_=settings.TWILIO_FROM,     # Your Twilio number (SMS-capable)
        body="Hej! Detta är ett ytterligare test2 från Python och Twilio 🇸🇪"
    )

#ret = send_sms( "SUBJECT HERE " )
#print(f"Message sent! SID: {ret}")
