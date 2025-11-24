# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from datetime import timezone
import glob
import logging 
import random
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
import os
import time
import json
import re
import sys, traceback
logger = logging.getLogger(__name__)



def create_url_safe_base64(s):
    sha256_hash = hashlib.sha256(s.encode('ascii')).digest()
    url_safe_base64_encoded = base64.urlsafe_b64encode(sha256_hash).decode('ascii')
    return url_safe_base64_encoded

def get_global_password( user ) :
    key = create_url_safe_base64( settings.SECRET_KEY)
    fernet = Fernet( key )
    if user.email :
        handle = str( user.email )
    else :
        handle = str( user.username )
    if user.username == 'super' :
        handle = 'super'
    fn = 'secret'
    p = f"/subdomain-data/auth/secrets/{handle}/{fn}.txt"
    password = None
    if os.path.exists( p ) :
        json_secrets_enc = open(p,"r").read()
        json_secrets = fernet.decrypt(json_secrets_enc).decode()
        secrets = json.loads(json_secrets)
        # DONT WORRY! ALL THESE ARE ENCRYPTED PASSWORDS HASHES 
        password = secrets['password']
    return password


def get_safe_ips( user ):
    if user.email :
        handle = str( user.email )
    else :
        handle = str( user.username )
    if user.username == 'super' :
        handle = 'super'
    fn = 'ips'
    p = f"/subdomain-data/auth/secrets/{handle}/ips/"
    if os.path.exists( p ) :
        ips = [ os.path.basename(i) for i in glob.glob(f"{p}/*") ]
    else:
        ips = []
    return ips


def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "a").close()


def save_safe_ips( user ,ip ):
    if user.email :
        handle = str( user.email )
    else :
        handle = str( user.username )
    if user.username == 'super' :
        handle = 'super'
    fn = 'ips'
    p = f"/subdomain-data/auth/secrets/{handle}/ips/"
    os.makedirs(p,exist_ok=True)
    touch( os.path.join( p, ip ) )
    ips = [ os.path.basename(i) for i in glob.glob(f"{p}/*") ]
    return ips





def get_otp_secret( user ,ekey=None):
    key = create_url_safe_base64( settings.SECRET_KEY)
    fernet = Fernet( key )
    if user.email :
        handle = str( user.email )
    else :
        handle = str( user.username )
    if user.username == 'super' :
        handle = 'super'
    fn = 'secret'
    p = f"/subdomain-data/auth/secrets/{handle}/{fn}.txt"
    if os.path.exists( p ) :
        json_secrets_enc = open(p,"r").read()
        json_secrets = fernet.decrypt(json_secrets_enc).decode()
        secrets = json.loads(json_secrets)
        # DONT WORRY! ALL THESE ARE ENCRYPTED PASSWORDS HASHES 
        #password1 = user.password
        #password2 = secrets['password']
        #password_unchanged = ( str( password1 ) == str( password2  ) )
        #print(f" {password_unchanged} PASSWORD1 = {password1} PASSWORD2={password2}")
        #if not password_unchanged :
        #    delete_otp_secret( user )
        #    return None
    else :
        return None
    encoded_secret = secrets['secret']
    password_hash = create_url_safe_base64( ekey )
    fernet = Fernet( password_hash)
    try :
        secret =  fernet.decrypt(encoded_secret).decode()
    except Exception as e :
        secret = None
    return secret


    

def delete_otp_secret( user ):
    if user.email :
        handle = str( user.email )
    else :
        handle = str( user.username )
    if user.username == 'super' :
        handle = 'super'
    fn = 'secret'
    p = f"/subdomain-data/auth/secrets/{handle}/{fn}.txt"
    if os.path.exists( p ) :
        os.remove(p)


def save_otp_secret( user, secret, ekey=None ):
    if not ekey :
        return secret
    if user.email :
        handle = str( user.email )
    else :
        handle = str( user.username )
    if user.username == 'super' :
        handle = 'super'
    p = f"/subdomain-data/auth/secrets/{handle}"
    os.makedirs( p , exist_ok=True)
    key = create_url_safe_base64( ekey )
    fernet = Fernet( key )
    encrypted_otp_secret = fernet.encrypt( secret.encode() )
    secrets =  {'username' : user.username, 'secret' : encrypted_otp_secret.decode() , 'password' : user.password } # , 'key' : key, 'ekey' : ekey }
    key = create_url_safe_base64( settings.SECRET_KEY)
    fernet = Fernet( key )
    json_secrets = json.dumps(secrets)
    json_secrets_enc = fernet.encrypt( json_secrets.encode() )
    fn = ''.join([random.choice('0123456789abcdef') for _ in range(8)])
    fn = 'secret'
    filename = f"{p}/{fn}.txt"
    fp = open(filename,"wb")
    fp.write(json_secrets_enc )
    return secret



def pil_image_to_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")  # You can use "JPEG" or other formats
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def validate_otp_token( user ,token ,secret=None, ekey=None) :
     if not secret :
         secret = get_otp_secret( user, ekey )
     totp = pyotp.TOTP(secret);
     s = totp.now();
     is_valid = totp.verify(token,None, 2)
     return is_valid


