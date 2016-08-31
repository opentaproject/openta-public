'''
Middleware to simulate a slow connection
'''

import time
import random


def simulate_slow(get_response):
    def middleware(request):
        response = get_response(request)
        time.sleep(random.uniform(0, 2))
        return response

    return middleware
