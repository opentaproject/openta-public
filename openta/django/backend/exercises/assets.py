# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Asset file handling."""
import urllib3
import datetime
import logging
import glob
import os
import shutil
import re
import subprocess
import tarfile
import time
import zipfile
from subprocess import PIPE

from course.models import Course, pytztimezone, tzlocalize
from exercises.models import Exercise
from image_utils import compress_pil_image_timestamp
from slugify import slugify

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

asset_types = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".svg",
    ".tiff",
    ".tif",
    ".png",
    ".gif",
    ".py",
    ".csv",
    ".txt",
    ".m",
    ".tex",
    ".gz",
    ".tgz",
    ".zip",
    ".xlsx",
    ".m",
    ".npy",
    ".log",
    ".xml",
    ".mplt",
    ".gplt",
    ".pov",
    ".log",
    ".inc",
    ".key",
    ".js",
    ".css",
    ".pg",
    ".pl",
    ".pm",
    ".html",
    ".xml",
    ".md",
    ".mmd",
)


editables = [
    "tex",
    "txt",
    "py",
    "mplt",
    "gplt",
    "csv",
    "pov",
    "log",
    "inc",
    "js",
    "css",
    "pl",
    "pm",
    "pg",
    "xml",
    "m",
    "md",
    "mmd",
]


runnables = [
    "py",
    "mplt",
    "gplt",
    "tex",
    "pov",
    "m",
    "md",
    "pdf",
]


logger = logging.getLogger(__name__)

def squashdir( path , excluded=[]):
    if os.path.exists(path):
        for root, d, files in os.walk(path):
            for file in files:
                dirname = root.split('/')[-1];
                if not dirname in excluded  and not root in [path] :
                    fullpath = os.path.join(root, file)
                    shutil.move(fullpath,path)
                    #print(f"{dirname} FILE {root} + {file} => {fullpath}")
        dirs = [ i for i in os.listdir( path ) if os.path.isdir( os.path.join( path, i ) ) ]
        for dirname in dirs:
                full_path = os.path.join(path, dirname)
                if os.path.isdir(full_path) and  not dirname in excluded :
                    shutil.rmtree( full_path)



def list_assets(path, types):
    tz = pytztimezone(settings.TIME_ZONE)
    if os.path.exists(path):
        all_files = os.listdir(path)
        files = []
        for file in all_files:
            full_path = os.path.join(path, file)
            size = os.path.getsize(full_path)
            seconds = os.path.getmtime(os.path.join(path, file))
            time.time()
            date = tzlocalize(datetime.datetime.fromtimestamp(seconds)).strftime("%Y-%m-%d %H:%M:%S")
            if not file in ["exercise.xml"]:
                files = files + [[file, str(date), str(size)]]
        assets = [
            {"filename": asset[0], "date": asset[1], "size": asset[2]}
            for asset in files
            if asset[0].lower().endswith(types)
        ]
        sorted_assets = sorted(assets, key=lambda d: d["date"], reverse=True)
        return {"files": sorted_assets, "editables": editables, "runnables": runnables}
    else:
        return {"files": []}


def has_asset(path, asset):
    file_path = os.path.join(path, asset)
    return os.path.isfile(file_path)


def permitted_file_name(member):
    member = str(member)
    if member == "exercisekey" :
        return False
    return True
    #if member == "exercise.xml":
    #    return True
    #if member == "exercisekey":
    #    return False
    #splits = member.split(".")
    #if len(splits) > 0:
    #    extension = "." + splits[-1]
    #    if not extension in asset_types:
    #        return False
    #if "/" not in member and not (member[0] == ".") and not (member[0] == "_"):
    #    return True
    #return False


def extract_exercise_archive(path, asset_file, types, course_key):
    print(f"EXTRACE_EXERCISE_ARCHIVE {path} {asset_file} ")
    subdomain = path.split('/')[2]
    db = subdomain
    extension = asset_file.name.split(".")[-1]
    contains_exercise_xml = False
    filelist_raw = ""
    skipped = ""
    historyskips = 0
    unzipped = False;
    if "zip" in extension:
        unzipped = True
        try:
            filelist = ""
            with zipfile.ZipFile(asset_file) as myzip:
                for member in myzip.namelist():
                    # print(f"member = {member}")
                    filelist_raw = filelist_raw + str(member) + ", "
                    if member in ["exercise.xml"]:
                        contains_exercise_xml = True
                    if "__MACOSX" in str(member):
                        return {"error": "Use zip -r ../file.zip . from the command line to zip a directory. "}
                    if permitted_file_name(member):
                        myzip.extract(member, path)
                        filelist = filelist + str(member) + ", "
                    else:
                        if not "history" in str(member):
                            skipped = skipped + str(member) + ", "
                        else:
                            historyskips += 1
                            if historyskips <= 2:
                                skipped = skipped + str(member) + ", "
                            else:
                                skipped = skipped + "."

        except zipfile.BadZipFile as e:
            logger.error("zip extract error: " + asset_file.name + " " + str(e))
            return {"error": "Error extracting  zipfile : " + asset_file.name}

    elif  extension in ['gz','tgz'] :
        unzipped = True
        try:
            temp_file_path = asset_file.temporary_file_path()
            filelist = ""
            with tarfile.open(temp_file_path) as mytar:
                for member in mytar.getmembers():
                    filelist_raw = filelist_raw + str(member) + ", "
                    if member in ["exercise.xml"]:
                        contains_exercise_xml = True
                    if permitted_file_name(member):
                        mytar.extract(member, path)
                        filelist = filelist + member.name + ", "
                    else:
                        skipped = skipped + str(member) + ", "
        except tarfile.TarError as e:
            logger.error("tar extract error: " + asset_file.name + " " + str(e))
            return {"error": "Error extracting  tarfile : " + asset_file.name}
    if unzipped :
        squashdir( path, ['Trash','history','__pycache__'] )
    if contains_exercise_xml:
        try:
            dbcourse = Course.objects.using(db).get(course_key=course_key)
            Exercise.objects.add_exercise_full_path(path, dbcourse,db)
        except ObjectDoesNotExist as e:
            logger.error("UNABLE TO RECREATE EXERCISE " + str(e))
            return {"error": "Unable to create exercise. Perhaps exercise.xml is missing"}
    if filelist == "":
        return {
            "error": f"ERROR: No subdirectories are extracted. Use zip -r ../file.zip . from the directory to zip a directory: Attempted to extract {skipped} "
        }
    else:
        msg = "Extracted: " + filelist
        if not skipped == "":
            msg = msg + f" Skipped = {skipped}"
        return {"error": msg}


def add_asset(path, asset_file, types, course_key, is_staff=False):
    """Create asset from uploaded file.

    Args:
        path (str): Path where asset is to be saved.
        asset_file (UploadedFile): Django uploaded file object.
        types (list(str)): List of approved file endings.

    Returns:
        dict: ::

            error (str): Error message
            success (str): Success message

    """
    subdomain = path.split('/')[2];
    print(f"ADD_ASSET {path}")
    subdomain = path.split('/')[2];
    db = subdomain
    try:
        filename, file_extension = os.path.splitext(asset_file.name)
        new = slugify(filename) + file_extension
        asset_file.name = new
        file_path = os.path.join(path, asset_file.name)
        illegals = ["<", "/", ">", ":", "\\", '"', "/", "|", "?", "*", "[", "]"]
        for c in illegals:
            if c in asset_file.name:
                return {"error": "File contains an illegal character %s " % c}
        if not asset_file.name.lower().endswith(types):
            return {"error": "File type not allowed, valid filetypes are: " + ", ".join(types)}
        extension = asset_file.name.split(".")[-1]
        if os.path.isfile(file_path):  # and is_staff : # and not extension in editables:
            t = time.localtime()
            current_time = time.strftime("%Y-%m-%d-%H-%M-%S", t)
            os.rename(file_path, f"{file_path}-{current_time}.txt")
        # if os.path.isfile(file_path) and not extension in editables:
        #    return {"error": "File already exists. You must delete the old file before reuploading. "}
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
        if is_staff and extension in ("zip", "gz","tgz"):
            # print("EXTRACT_EXERCISE_ARCHIVE")
            extract_exercise_archive(path, asset_file, types, course_key)
            # print(f"RET = {ret}")
        try:
            with open(file_path, "wb") as asset:
                for chunk in asset_file.chunks():
                    asset.write(chunk)
        except IOError:
            return {"error": "Couldn't write to asset file " + file_path}
        if (not is_staff) and extension.lower() in ("jpg", "png", "jpeg"):
            compress_pil_image_timestamp(file_path)

        # if is_staff and extension in ("tex"):
        #    texbase = asset_file.name.split(".tex")[0]
        #    pdflatex = subprocess.Popen(["pdflatex", texbase], cwd=path, text=True)
        #    pdflatex.wait()
        #    full_base = re.sub(f".{extension}$", "", file_path)
        #    print(f"FULL BASE = {full_base}")
        #    os.rename(f"{full_base}.log", f"{full_base}.log.txt")
        #    return ["success", "pdflatex run"]

        # if is_staff and extension in ["mplt", "gplt"]:
        #    filename = asset_file.name
        #    pyexec = subprocess.Popen(["python", filename], cwd=path, text=True)
        #    pyexec.wait()
        #    return ["success", "mplt ran"]
        return ["success", f"Wrote file {filename}"]
    except Exception as e:
        if file_extension in ["zip", "gz"]:
            return [
                "error",
                f" {type(e).___name__} Unanticipated error occured in file upload. To create compatible zip file:  <br/><b> zip -r ../file.zip .  </b><br/> Check your filename type  and check your file is not corrupted or huge.",
            ]
        else:
            return ["error", f"File has an upload error {e}"]


def delete_asset(path, asset_filename):
    file_path = os.path.join(path, asset_filename)

    if not os.path.isfile(file_path):
        return {"error": "No such file!"}
    try:
        trashpath = os.path.join(path, "Trash")
        os.makedirs(trashpath, exist_ok=True)
        newpath = os.path.join(trashpath, asset_filename)
        os.rename(file_path, newpath)
    except IOError:
        return ["error", "Couldn't delete asset file " + file_path]
    if os.path.isfile(file_path):
        return ["error", "Couldn't delete asset file " + file_path]

    return ["warning", "Moved file to trash"]


def run_asset(path, asset_filename):
    file_path = os.path.join(path, asset_filename)
    returncode = 0
    tbeg = time.time()
    try:
        if not os.path.isfile(file_path):
            return ["error", "No such file!"]

        filename, file_extension = os.path.splitext(asset_filename)
        file_path = os.path.join(path, asset_filename)
        extension = asset_filename.split(".")[-1]
        is_staff = True
        ns = (time.time(), time.time())
        times = (time.time(), time.time())
        debug = ""
        if is_staff and extension in ("pdf") :
            from .mathpix import mathpix
            filebase = asset_filename.split(".pdf")[0]
            tex_exists = os.path.exists( os.path.join( path, f"{filebase}.tex") )
            assert not tex_exists , f'Tex file {filebase}.tex exists and mmd wont be created' 
            res = mathpix(file_path,'mmd')
            outfile = os.path.join(path,f"mathpix-{filebase}.mmd" )
            o = open(outfile,"w")
            o.write(res)
        elif is_staff and extension in ("tex"):
            texbase = asset_filename.split(".tex")[0]
            pyexec = subprocess.Popen(
                ["lualatex", "-interaction=nonstopmode", texbase], cwd=path, stderr=PIPE, stdout=PIPE
            )
            pyexec.wait(timeout=settings.SUBPROCESS_TIMEOUT)
            full_base = re.sub(f".{extension}$", "", file_path)
            os.rename(f"{full_base}.log", f"{full_base}.log.txt")
            os.utime(file_path, times)  # SET MODIFY TIME TO LIST THE FILE AT THE TOP
            returncode = pyexec.returncode
            s = pyexec.stderr
            st = pyexec.stdout.read().decode("ascii")
            logger.error(f"ST = {st}")
            matches = re.findall(r"(.*Error.*|.*Warning.*)", st, re.MULTILINE)
            st = "\n".join(matches)
            os.utime(file_path, times)  #

        elif is_staff and extension == "md":
            texbase = asset_filename.split(".md")[0]
            fileout = f"{file_path}.tex"
            pandoc = "pandoc"
            pyexec = subprocess.Popen( [ pandoc  , "--verbose" , "--from","markdown+tex_math_single_backslash",   f"{texbase}.md","-o", f"{texbase}.pdf"], cwd=path, stderr=PIPE , stdout=PIPE)
            pyexec.wait(timeout=settings.SUBPROCESS_TIMEOUT)
            returncode = pyexec.returncode
            s = pyexec.stdout
            content = s.read()
            s = pyexec.stderr
            content = s.read()
            st = s


        elif is_staff and extension in ["mplt", "gplt"]:
            filename = asset_filename
            pyexec = subprocess.Popen(["python", filename], cwd=path, text=True, stderr=PIPE)
            pyexec.wait(timeout=settings.SUBPROCESS_TIMEOUT)
            returncode = pyexec.returncode
            s = pyexec.stderr
            st = s.read()
            st = re.sub("\^+", "", st)
            st = "line " + st.split("line")[-1]
            times = (time.time(), time.time())
            os.utime(file_path, times)  # SET MODIFY TIME TO LIST THE FILE AT THE TOP

        elif is_staff and extension in ["m"]:
            filebase = asset_filename.split(".m")[0]
            math = "/usr/local/bin/math"
            pyexec = subprocess.Popen( [ math, "-script", f"{filebase}.m"], cwd=path, stderr=PIPE , stdout=PIPE)
            MATHEMATICA_TIMEOUT = 2 * settings.SUBPROCESS_TIMEOUT
            pyexec.wait(timeout=MATHEMATICA_TIMEOUT)
            returncode = pyexec.returncode
            s1 = pyexec.stdout
            content1 = ( s1.read() ).decode('utf-8')
            s2 = pyexec.stderr
            content2 = s2.read().decode('utf-8')
            print(f"CONTENTS = {content1} {content2}")
            outfile = os.path.join(path,f"{filebase}.txt" )
            o = open(outfile,"w")
            o.write(f"STDOUT={content1}\n")
            if content2 :
                o.write(f"STDERR={content2}")
            o.close()
            

        elif is_staff and extension in ["pov"]:
            filename = asset_filename
            try:
                pyexec = subprocess.run(
                    f"povray {filename} ",
                    cwd=path,
                    shell=True,
                    capture_output=True,
                    check=True,
                    timeout=settings.SUBPROCESS_TIMEOUT,
                )
                returncode = pyexec.returncode
                s = (pyexec.stdout).decode("ascii")
                times = (time.time() + 1, time.time() + 1)
                os.utime(file_path, times)  # SET MODIFY TIME TO LIST THE FILE AT THE TOP
                if returncode == 0:
                    return ["success", f" Ran {asset_filename}   "]
                else:
                    s = pyexec.stderr
                    s = (pyexec.stdout).decode("ascii")
                    return ["error", f" Ran {asset_filename}  {returncode}  {s}   "]
            except subprocess.TimeoutExpired as e:
                return ["error", f"timeout {asset_filename} . Try again ; otherwise shorten the program.      "]
            except Exception as e:
                return ["error", f"Failed {asset_filename} { type(e).__name__}  {str(e)}      "]

        delta = int(10 * (time.time() - tbeg) + 1) / 10.0
        if returncode == 0:
            if delta < 0.7 * settings.SUBPROCESS_TIMEOUT:
                return ["success", f" Successfully ran {asset_filename} in { delta} seconds. "]
            else:
                return [
                    "warning",
                    f"Getting close to run limit of {settings.SUBPROCESS_TIMEOUT} seconds. Successfully ran {asset_filename} in { delta} seconds. ",
                ]

        else:
            return ["warning", f" {asset_filename} failed {st} "]
    except Exception as e:
        logger.error(f" ERROR  {type(e).__name__} {str(e)}  ")
        return ["error", f"the file {asset_filename} gave errors {str(e)} "]
