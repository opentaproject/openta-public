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
                self.client.headers['X-CSRFToken'] = csrftoken
                self.client.cookies['csrftoken'] = csrftoken
                with self.client.post(
                    '/login/',
                    data={
                        'username': 'student',
                        'password': 'learning',
                        'csrfmiddlewaretoken': csrftoken,
                    },
                    catch_response=True,
                ) as response:
                    pprint(response)
                print("Sent login info")
                if self.check_loggedin():
                    print("Login confimed")
                else:
                    print("Login failed!")
            else:
                print("No csrf token")

    def check_loggedin(self):
        loggedinrequest = self.client.get('/loggedin/')
        pprint(loggedinrequest.content)
        loggedin = loggedinrequest.json()
        return 'username' in loggedin

    # @task(1)
    def get_exercises(self):
        r = self.client.get("/exercises")
        self.exercises = r.json()
        if r.status_code > 300:
            print("/exercises failed")

    @task(1)
    def exercises_tree(self):
        r = self.client.get("/exercises/tree")
        if r.status_code > 300:
            print("/exercises failed")

    @task(3)
    def exercise_random_folder(self):
        # exercises = self.client.get("/exercises").json()
        self.get_exercises()
        exercise = random.choice(self.exercises)
        folder = self.client.get("/exercise/" + exercise['exercise_key'] + "/samefolder")
        # print(folder.json())

    @task(10)
    def exercise_load(self):
        try:
            exercise = random.choice(self.exercises)
            json = self.client.get("/exercise/" + exercise['exercise_key'] + "/json")
            xml = self.client.get("/exercise/" + exercise['exercise_key'] + "/xml")
            state = self.client.get("/exercise/" + exercise['exercise_key'])
        except IndexError:
            pass


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 5000
