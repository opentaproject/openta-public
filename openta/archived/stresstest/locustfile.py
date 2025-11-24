# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from locust import HttpLocust, TaskSet, task
from locust import InterruptTaskSet
import requests
import random
from pprint import pprint

requests.packages.urllib3.disable_warnings()  # disable SSL warnings


class UserBehavior(TaskSet):
    def __init__(self, *args, **kwargs):
        super(UserBehavior, self).__init__(*args, **kwargs)
        self.exercises = []
        self.exercisesdict = {}
        self.loaded_exercises = {}
        self.csrftoken = ""

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.client.verify = False
        if self.check_loggedin():
            print("on_start: Already logged in")
        else:
            r = self.client.get("/login/")
            if 'csrftoken' in r.cookies:
                csrftoken = r.cookies['csrftoken']
                self.csrftoken = csrftoken
                self.client.headers['Referer'] = self.client.base_url
                # self.client.headers['X-CSRFToken'] = csrftoken
                # self.client.cookies['csrftoken'] = csrftoken
                with self.client.post(
                    '/login/',
                    data={
                        'username': 'student',
                        'password': settings.SUPERUSER_PASSWORD ,
                        'csrfmiddlewaretoken': csrftoken,
                    },
                    catch_response=True,
                ) as response:
                    pass
                    # print(response.request.cookies)
                    # pprint(response)
                print("Sent login info")
                if self.check_loggedin():
                    print("Login confimed")
                    self.get_exercises()
                else:
                    print("Login failed!")
            else:
                print("No csrf token")

    def get_csrf(self):
        res = self.client.get('/login/')
        if 'csrftoken' in res.cookies:
            return res.cookies['csrftoken']
        else:
            ''

    def check_loggedin(self):
        loggedinrequest = self.client.get('/loggedin/')
        pprint(loggedinrequest.content)
        loggedin = loggedinrequest.json()
        return 'username' in loggedin

    # @task(1)
    def get_exercises(self):
        r = self.client.get("/exercises")
        self.exercisesdict = r.json()
        self.exercises = self.exercisesdict.values()
        if r.status_code > 300:
            print("/exercises failed")

    # @task(1)
    def exercises_tree(self):
        r = self.client.get("/exercises/tree")
        if r.status_code > 300:
            print("/exercises failed")

    # @task(3)
    def exercise_random_folder(self):
        # exercises = self.client.get("/exercises").json()
        self.get_exercises()
        exercise = random.choice(self.exercises)
        folder = self.client.get("/exercise/" + exercise['exercise_key'] + "/samefolder")
        # print(folder.json())

    @task(10)
    def check_random_answer(self):
        try:
            key = random.choice(self.loaded_exercises.keys())
            json = self.loaded_exercises[key]
            question_key = json['exercise']['question'][0]['@attr']['key']
            token = self.get_csrf()
            with self.client.post(
                '/exercise/' + key + '/question/' + question_key + '/check',
                json={'answerData': '1'},
                headers={
                    'X-CSRFToken': token,
                    #'Accept': 'application/json',
                    #'X-Requested-With': 'XMLHttpRequest'
                },
                catch_response=True,
            ) as response:
                if 'correct' not in response.json():
                    print("Exercise check failed!")
                # print(response)
                # pass
                print(response.json())
        except IndexError:
            pass

    @task(2)
    def exercise_load(self):
        try:
            self.exercises_tree()
            self.exercise_random_folder()
            exercise = random.choice(self.exercises)
            json = self.client.get("/exercise/" + exercise['exercise_key'] + "/json")
            parsedjson = json.json()
            # print(parsedjson)
            self.loaded_exercises[exercise['exercise_key']] = parsedjson
            # xml = self.client.get("/exercise/" + exercise['exercise_key'] + "/xml")
            state = self.client.get("/exercise/" + exercise['exercise_key'])
        except IndexError, KeyError:
            pass


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 3000
    max_wait = 10000
