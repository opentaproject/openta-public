from django.test import TestCase
from .linear_algebra import linear_algebra


class LinearAlgebraTest(TestCase):
    def test_variable(self):
        variables = [
            {'name': 'x', 'value': '2'},
            {'name': 'y', 'value': '2 kg'},
            {'name': 'z', 'value': 'sample(3)'},
        ]
        res = linear_algebra(variables, 'x*y*z*(1/(1+z)+z/(1+z))+1-sqrt(1)', 'x*y*z')
        self.assertEqual(res['correct'], True)

    def test_variable(self):
        variables = [{'name': 'v1', 'value': '[1,0,0]'}, {'name': 'v2', 'value': '[0,1,0]'}]
        res = linear_algebra(variables, 'dot(v1,v2)', 'dot(v1,[1,0,0])')
        self.assertEqual(res['correct'], True)
