# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError

from lxml import etree;
import re

class Command(BaseCommand):

    help = "denest  answers"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("--subdomain",  dest="subdomain" , type=str, default="", help="filter by answerpks")
        parser.add_argument("--f",  dest="f" , type=str, default="", help="file to be denested")

    def handle(self,*args,**kwargs):
        print(f"ARGS = {args} kwargs={kwargs}")
        filename = kwargs.get("f",None)
        print(f"FILENAME = {filename}")
        f = file.open(f,"r");
        xml = f.read();
        print(f"XML = {xml}")
        target = etree.fromstring(xml);



    
def denest( target ):

    for e in target.iter(tag="text"):
        print(f"TAG = {e.tag}")
        ixml = '';
        head = e.text;
        att = e.attrib;
        print(f"ATT = {att}")
        didixml = False;
        try :
            
            p = e;
            ixml =   str(etree.tostring(p ));
            ixml = re.sub(r"<text[^\>]*>","",ixml);
            print(f"IXML = {ixml}")

            ixml = ixml.replace("</text>","");
            ixml = re.sub(r"b\'","",ixml,count=1);
            ixml = ixml.strip('\'');
            print(f"IXML = {ixml}")
            didixml = True;
            
        except :
            pass
        txt =  ixml 
    
        if e.tail and e.tail.strip() :
            
            txt =  e.tail.strip();
        nx = f"<text>{head} {txt} </text>";
        print(f"nx = {nx}")
        enew  = etree.fromstring(nx);
        for k in att.keys() :
            print(f"{k}, {att[k]}")
            enew.set(k,att[k]);
        #enew.attrib = att;
        pp = e.getparent();
        if didixml :
            pp.remove(e);
        pp.append(enew)
        
    return target;
        
