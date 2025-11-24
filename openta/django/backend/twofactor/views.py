# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from datetime import timezone
from django.contrib.auth.hashers import check_password
from cryptography.fernet import Fernet
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth.models import Group, User
import qrcode, pyotp;
from django.contrib.auth.decorators import login_required
from django.views.decorators.clickjacking import xframe_options_exempt
from django_otp.forms import OTPTokenForm
from django.contrib import messages
import hashlib
import base64
from PIL import Image
import logging
import io
from django.contrib.auth import logout as syslogout
import os
import time
import json
from django.shortcuts import redirect, render
from utils import get_subdomain, get_subdomain_and_db
import re
from twofactor.utils import create_url_safe_base64, get_otp_secret, delete_otp_secret, save_otp_secret, pil_image_to_base64, validate_otp_token, get_global_password, get_safe_ips, save_safe_ips




class twofactorauth:

    db = None
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"AUTHENGICATE")
        #safe_ips = get_safe_ips( request.user )
        #print(f"SAFE IPS = {safe_ips}")
        subdomain,db = get_subdomain_and_db( request )
        twofactorauth.db = db
        try :
            user = User.objects.using(db).get(username=username)
            if not user.is_staff :
                return None
        except ObjectDoesNotExist:
            return None
        if request.session.get('hijacked', False ):
            return user
        storage = messages.get_messages(request)
        #for _ in storage:
        #    pass 
        #if re.match(r'[0-9][0-9][0-9][0-9][0-9][0-9]',password ) :
        #    print(f"MATCH FOUND")
        #    user = User.objects.using(db).get(username=username)
        #    is_valid = validate_otp_token( user, password , ekey )
        #    if is_valid and settings.ALLOW_OTP_ONLY :
        #        request.session['OTP-VALID'] = True
        #        request.session['RESET-PASSWORD'] = True
        #        return user
        local_password = user.password
        global_password = get_global_password(user)
        if global_password and not str( local_password) == str( global_password ):
            ok  = check_password( password, global_password )
            if ok :
                user.password = global_password
                user.save() 
                messages.success(request, "Course was updated with your latest password. Try login again")
                return user
        if '@' in username:
            try  :
                user = User.objects.using(db).get(email=username)
            except ObjectoDoesNotExist as err  :
                return None
            isvalid = user.check_password(password)
        else :
            return None

    def get_user(self, user_pk):
        from django.contrib.auth.models import Group, User
        try:
            user = User.objects.using(self.db).get(pk=user_pk)
            return user
        except User.DoesNotExist:
            return None


@login_required
@xframe_options_exempt
def otp_validate(request):
    subdomain,db = get_subdomain_and_db( request )
    print(f"OTP_VALIDATE")
    in_progress = request.session.get('OTP-IN-PROGRESS', False )
    if in_progress :
        delete_otp_secret( request.user )
        return redirect("/logout/?next=login")
    data = request.META
    action = request.POST.get('ACTION',None)
    if action == 'Cancel' :
        syslogout(request)
        return redirect('/')
    user = request.user
    otpform = OTPTokenForm
    form = otpform(request.user, request)
    ekey = request.session.get('USER-ENCRYPTION-KEY',None )
    if ekey :
        secret = get_otp_secret( user, ekey )
    else :
        secret = None
    body = request.body
    if not secret :
        randkey =  pyotp.random_base32();
        #openta = settings.OPENTA_SERVER
        if settings.OPENTA_SERVER == 'localhost' :
            openta = 'localhost'
        else :
            openta = 'OpenTA'
        totp_uri = f"otpauth://totp/{openta}:{user}?secret={randkey}&issuer={openta}"
        secret = randkey;
        qr = qrcode.make(totp_uri)
        img_str = pil_image_to_base64( qr )
        messages.success(request, f"Scan the following into your OTP authenticator app.  Save a screenshot for your other 2FA devices and save the secret below to enable other devices.  THIS INFORMATION WILL NOT BE SHOWN AGAIN! ")
        secret = save_otp_secret( user , randkey, ekey )
        request.session['OTP-IN-PROGRESS'] = True
        return render(request, 'show_qrcode.html', {'image_base64': img_str, 'secret' : secret})
        

    #print(f"OTP_VALIDATE {data}")
    #if request.method == "POST":
    #    if request.POST["action"] == "cancel":
    #        return redirect("/logout/?next=login")
    if not request.body :
         return render(request, "otp_validate.html", {"form": form})
    else :
        token = request.POST.get('otp_token','')
        user_ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if user_ip_address:
            ip = user_ip_address.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", None)
        if token :
            is_valid = validate_otp_token( user, token ,secret, ekey  )
            if is_valid :
                ips = save_safe_ips(user ,ip)
                request.session['OTP-VALID'] = True
                request.session['REQUIRE-OTP'] = False
            else :
                messages.success(request,"Invalid code")
            return redirect('/')
    return render(request, "otp_validate.html", {"form": form})


