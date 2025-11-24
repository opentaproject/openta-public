from django.conf import settings
import sys


def dprint(s, *args):
    if settings.SHOW_TIMING:
        caller = sys._getframe().f_back.f_code.co_name
        print(f" {s}                                {caller} ")
    return
