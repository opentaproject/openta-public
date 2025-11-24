# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from django.http import QueryDict
import subprocess
from django.core.cache import caches
import threading
import os
import sys
import re
import json
import time
import shutil
import traceback
import datetime

import psycopg2.extensions
from utils import get_subdomain, get_subdomain_and_db, get_subdomain_and_db_, db_info_var, user_info_var

from django.conf import settings

# from django.contrib.sites.models import Site
# from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import logout as syslogout
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import (
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS, ConnectionDoesNotExist, load_backend
DOLOG = False




def verify_or_create_database_connection(subdomain):
    if DOLOG or subdomain == None or subdomain == '' :
        logger.error(f" XXX MIDDLEWARE VERIFY_OR_CREATE_DATABASE_CONNECTION HAS SUBDOMAIN = {subdomain}")
    if not settings.MULTICOURSE:
        return
    db_name = subdomain
    try:
        c = connections[subdomain]
    except ConnectionDoesNotExist:
        settings.DATABASES[db_name] = add_database(db_name)
        create_connection(db_name)


def check_connection(db):
    if DOLOG or db == None or db == '' :
        logger.error(f" XXX MIDDLEWARE CHECK_CONNECTION HAS SUBDOMAIN = {db}")
    if not settings.MULTICOURSE:
        return
    try:
        connections[db]
    except ConnectionDoesNotExist:
        settings.DATABASES[db] = add_database(db)
        create_connection(db)


def create_connection(alias=DEFAULT_DB_ALIAS):
    if not settings.MULTICOURSE:
        return
    if DOLOG or alias == None or alias == '' :
        logger.error(f" XXX MIDDLEWARE CREATE_CONNECTION HAS ALIAS = {alias}")
    # connections.ensure_defaults(alias)
    # connections.prepare_test_settings(alias)
    er = "A"
    try:
        db = connections.databases[alias]
        er = er + "B"
        backend = load_backend(db["ENGINE"])
        er = er + "C"
        r = backend.DatabaseWrapper(db, alias)
        return r
    except Exception:
        logger.error(f" XXX MIDDLEWARE CREATE_CONNECTION_ERROR er={er} alias={alias} ")
        raise PermissionDenied(f" connection to {alias} failed ")


def add_database(x):
    if not settings.MULTICOURSE:
        return
    if DOLOG or x == '' :
        logger.error(f" XXX MIDDLEWARE X = {x} in add_database")
    ret = {}
    subdomain = x 
    if subdomain in settings.DATABASES :
        if DOLOG :
            logger.error(f"XXXX {subdomain} already exists in DATABASES ")
        return settings.DATABASES[subdomain]
    try:
        dbnamefile = settings.VOLUME + "/" + x + "/dbname.txt"
        if os.path.exists(dbnamefile):
            f = open(settings.VOLUME + "/" + x + "/dbname.txt")
            db_name = f.read()
            db_name = re.sub(r"\W", "", db_name)
            f.close()
            ret = {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_name,
                "USER": settings.PGUSER,
                "PASSWORD": settings.PGPASSWORD,
                "HOST": settings.PGHOST,
                "PORT": "5432",
                "ATOMIC_REQUESTS": True,
                "TIME_ZONE": "Europe/Stockholm",
                "CONN_HEALTH_CHECKS" : settings.CONN_HEALTH_CHECKS,
                "CONN_MAX_AGE" : settings.CONN_MAX_AGE,
                "AUTOCOMMIT": True,
                "OPTIONS" : {},
            }
            return ret
        else:
            raise SuspiciousOperation(f"Suspicious subdomain {x} does not exist")
    except Exception as e :
        raise PermissionDenied(f" {type(e).__name__} subdomain {x} does not exist - error 2")
    return ret


class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # subdomain = request.META['HTTP_HOST'].split('.')[0]
        subdomain = get_subdomain(request)
        if DOLOG :
            logger.error(f"XXX SAMESITE_MIDDLEWARE {subdomain}")
        settings.DB_NAME = subdomain
        settings.EXERCISES_PATH = "%s/%s/exercises" % (settings.VOLUME, subdomain)
        settings.SUBDOMAIN = subdomain
        settings.MEDIA_ROOT = "%s" % settings.VOLUME
        sessionid = "sessionid%s" % subdomain
        csrftoken = "csrftoken%s" % subdomain
        for cookie in [
            sessionid,
            csrftoken,
            "launch_presentation_return_url",
            "displayStyle",
            "csrf_cookie_name",
            "cookieTest",
        ]:
            if cookie in response.cookies:
                response.cookies[cookie]["samesite"] = "None"
                response.cookies[cookie]["secure"] = True
        return response


class SubpathMiddleware(MiddlewareMixin):
    def process_request(self, request, response=None):
        # domain = ( request.get_host()   ).split(':')[0]
        # subdomain = request.META['HTTP_HOST'].split('.')[0]
        subdomain = get_subdomain(request)
        settings.DB_NAME = subdomain
        settings.EXERCISES_PATH = "%s/%s/exercises" % (settings.VOLUME, subdomain)
        settings.SUBDOMAIN = subdomain
        settings.MEDIA_ROOT = "%s" % settings.VOLUME


def log_500_error(txt):
    logger.error(f" XXX MIDDLEWARE LOG_500_ERROR {txt}")
    server = settings.OPENTA_SERVER
    formatted_lines = traceback.format_exc()
    filename = f"/subdomain-data/{server}-error500.txt";
    for okpat in  [ '.accepted_renderer not set on Response' ] :
        if re.search(okpat, formatted_lines ) :
            logger.error(f" XXX MIDDLEWARE  DO NOT TRIGGER SMS due to EXEMPT {okpat} \n  ")
            return 
    x = str( datetime.datetime.now() )
    x = re.sub(r'[ :]+','-',x)
    fp = open(filename, 'a');
    fp.write(f"{x} : {txt}  {formatted_lines } \n" )
    try :
        shutil.copy('/tmp/gunicorn.err.log', f"/subdomain-data/{server}-{x}-gunicorn.err.log")
    except :
        pass
    try :
        s = settings.OPENTA_SERVER 
        for s in ['memcached','pgbouncer','db-server',server] :
            if s in formatted_lines :
                p = f"/subdomain-data/postgres/{s}-error"
                with open(p,'a') :
                    os.utime(p,None)

    except Exception as e :
        logger.error(f" XXX MIDDLEWARE CANNOT TOUCH {p} : {str(e)} ")


    try :
        os.remove('/tmp/healthy')
        fp.write(f"REMOVE /tmp/healthy")
    except :
        fp.write(f"REMOVE /tmp/healthy FAILED")
    fp.close

def connection_number( subdomain ):
    dbnamefile = settings.VOLUME + "/" + subdomain + "/dbname.txt"
    dbname = open(dbnamefile,"r").read()
    pguser = settings.PGUSER
    pgpassword = settings.PGPASSWORD
    conn = psycopg2.connect(f"dbname={dbname} user={pguser} password={pgpassword}")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pg_stat_activity;" )
    total_connections = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total_connections




def db_exists( subdomain ):
    exists = False 
    if DOLOG :
        logger.error(f"MIDDLEWARE DB_EXISTS {subdomain}")
    try :
        dbnamefile = settings.VOLUME + "/" + subdomain + "/dbname.txt"
        dbname = open(dbnamefile,"r").read()
        pguser = settings.PGUSER
        pgpassword = settings.PGPASSWORD
        conn = psycopg2.connect(f"dbname={dbname} user={pguser} password={pgpassword}")
        cur = conn.cursor()
        cur.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_schema = %s AND table_name = %s);", ("public", "auth_user",))
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
    except :
        logger.error(f"DB_EXISTS {subdomain} GIVES False ")
        exists = False
    return exists


def old_restore_db( subdomain ):
    env_vars = os.environ.copy()
    env_vars.update({
        'PGHOST': settings.DBHOST,
        'DBHOST': settings.DBHOST
        })
    database = open(os.path.join( settings.VOLUME, subdomain, "dbname.txt"),"r").read()
    dump_file= os.path.join( settings.VOLUME, subdomain, f"{dbfile}.db")
    #print(f"DATABASE={database} dump_file={dump_file}")
    #result = subprocess.run(['./db_restore', settings.SUBDOMAIN] ,env=env_vars, capture_output=True, text=True)
    #txt = result.stderr
    #logger.error(f"TXT = {txt}")
    #logger.error(f"TXT = {txt}")
    #response =  HttpResponseServerError(f"<h3>  Course {subdomain} was retrieved. Reload page in about 15 seconds. </h3>")
    #exists = db_exists( subdomain) 
    #if exists :
    #    response =  HttpResponseServerError(f"<h3>  Course {subdomain} was retrieved. Reload page. </h3>")
    #else  :
    #    response =  HttpResponseServerError(f"<h3>  Database for {subdomain} is damaged.  </h3>")
    response =  HttpResponseServerError(f"<h3>  Course {subdomain} is retrieved. Reload page in about 15 seconds. </h3>")
    return response

def restore_db( subdomain ):
    try :
        env_vars = os.environ.copy()
        env_vars.update({
            'PGHOST': settings.DBHOST,
            'DBHOST': settings.DBHOST,
            'PGUSER': settings.PGUSER,
            })
        txt = ''
        add_database( subdomain)
        database = open(os.path.join( settings.VOLUME, subdomain, "dbname.txt"),"r").read().strip()
        dump_file= os.path.join( settings.VOLUME, subdomain, f"{database}.db")
        print(f"DATABASE={database} dump_file={dump_file}")
        cmd1 = f"psql -U postgres -c \"DROP DATABASE IF EXISTS {database};\""
        cmd2 = f"psql -U postgres -c \"CREATE DATABASE {database} OWNER postgres;\""
        ip = env_vars.get("DB_SERVER_SERVICE_HOST",f"{settings.DBHOST}")
        cmd3 = f"pg_restore -U postgres --no-owner -d {database} -h {ip} {dump_file}"
        print(f"CMD1={cmd1}")
        print(f"CMD2={cmd2}")
        print(f"CMD3={cmd3}")
        print(f"{ip}")
        result = subprocess.run(cmd1,env=env_vars, shell=True, check=True, capture_output=True, text=True)
        txt1 = result.stderr
        print(f"TXT1={txt1}")
        result = subprocess.run(cmd2,env=env_vars, shell=True, check=True, capture_output=True, text=True)
        txt2 = result.stderr
        print(f"TXT2={txt2}")
        result = subprocess.run(cmd3,env=env_vars, shell=True, check=True, capture_output=True, text=True)
        txt3 = result.stderr
        print(f"TXT3={txt3}")
        subprocess.run(['python','manage.py','clear_cache','--all'])
        if not 'localhost' in settings.OPENTA_SERVER :
            subprocess.run(['supervisorctl','reload'])
        response =  HttpResponseServerError(f"<h3>  Course {subdomain} was retrieved. Reload page in about 30 seconds {txt1} {txt2} {txt3} </h3>")
    except: 
        response =  HttpResponseServerError(f"<h3>  Course {subdomain} was retrieved. Try again in about 30 seconds")
    return response


 




class SetBasicSessionVars(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # subdomain = request.META['HTTP_HOST'].split('.')[0]
        try:
            request.session['timing'] = time.time() 
            request.session['db'] = db_info_var.get();
            request.session['subdomain'] = db_info_var.get();
            request.session['username'] = user_info_var.get()
            request.session['sessionid'] = request.COOKIES.get('sessionid')
        except :
            logger.error(f"XXX MIDDLEWARE SESSION HAS NOT BEEN SET")
        response = self.get_response(request)
        return response





class DynamicSiteDomainMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # subdomain = request.META['HTTP_HOST'].split('.')[0]
        try:
            subdomain = request.META["HTTP_HOST"].split(".")[0].split(":")[0]
            if subdomain == '' :
                logger.error(f"DYNAMIC_SITE_DOMAIN_MIDDLEWARE GENERATES subdomain={subdomain}")
            db_info_var.set(subdomain)
            try :
                body = request.body
                data = QueryDict( body)
                username = data.get('username', request.COOKIES.get('username',None) )
                key = f"temp-{username}"
                caches['default'].set( key, subdomain,600 )
            except Exception as e :
                username = None
                user_info_var.set(username)
            db = subdomain
            settings.SUBDOMAIN = subdomain
            settings.DB_NAME = db
            try:
                # Ensure the alias exists in Django's connection handler without
                # creating an unnecessary standalone DatabaseWrapper instance.
                connections[subdomain]
            except ConnectionDoesNotExist as e :
                try:
                    pathok =  os.path.exists(os.path.join(settings.VOLUME, subdomain ))
                    if not pathok :
                        time.sleep(5)
                        return HttpResponseServerError(
                            f'<body style="text-align: center;"><button  style=" \
                            height: 80px; border-radius: 30px; margin-top: 10%; background-color:pink; font-size: 30px; ">  \
                            {subdomain} does not exist  </button> </body>'
                            )
                    exists = db_exists( db )
                    if not exists :
                        r = restore_db( subdomain )
                        return r
                    settings.DATABASES[db] = add_database(db)
                    # Let Django lazily initialize connections when first used.
                except PermissionDenied as e:
                    logger.error(f"PERMISSION DENIED ERROR = {str(e)} {type(e).__name__}")
                    return HttpResponseServerError( f'<body style="text-align: center;"><button  style=" height: 80px; border-radius: 30px; \
                            margin-top: 10%; background-color:pink; font-size: 30px; ">  {str(e)} </button> </body>')
            except Exception:
                logger.error("XXX MIDDLEWARE CONNECTION_EXCEPTION ERROR {subdomain} {str(e)} {type(e).__name__}")
                return HttpResponseServerError(f"<h3>  Uncaught server error </h3>")
            # try:
            #    current_site, created = Site.objects.get_or_create(domain=subdomain,)
            # except Site.DoesNotExist:
            #    messages.add_message(request, messages.ERROR, _('Site %s exists but is misconfigured.' % subdomain))
            #    return render(request, "base_failed.html")

            # request.current_site = current_site
            # settings.SITE_ID = current_site.id
            response = self.get_response(request)
            # Proactively close the per-subdomain connection to avoid
            # accumulating many open clients when accessing many subdomains
            # (e.g., via hijack or admin actions).
            try:
                if subdomain:
                    connections[subdomain].close()
            except Exception:
                # Best-effort; do not block response on close errors.
                pass
            return response
        except Exception as e:
            logger.error(f"XXX MIDDLEWARE Dymamic Domain middleware fail {type(e).__name__}")
            log_500_error(f"XXX MIDDLEWARE 500 error from DynamicDomainMiddleware {type(e).__name__} { str(e)} ")
            response = HttpResponseRedirect("/")
            request.session.modified = True
            for cookie in request.COOKIES:
                response.delete_cookie(cookie)
            syslogout(request)
            return response
