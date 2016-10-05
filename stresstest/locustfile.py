from locust import HttpLocust, TaskSet, task
from locust import InterruptTaskSet
import requests
from pprint import pprint

requests.packages.urllib3.disable_warnings()  # disable SSL warnings


class UserBehavior(TaskSet):
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

    @task(1)
    def profile(self):
        r = self.client.get("/")
        pprint(r)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 5000
