from exercises.question import register_question_type
import functools
import operator
import exercises.symbolic as symbolic
from exercises.util import compose

# import exercises.question


def parse_variables(variables):  # {{{
    rawvars = variables.split(';')
    pipeline = compose(
        functools.partial(filter, operator.truth),
        functools.partial(map, lambda x: x.split('=')),
        functools.partial(map, lambda x: {'name': x[0].strip(), 'value': x[1].strip()}),
    )
    variables = list(pipeline(rawvars))
    return variables  # }}}


def question_check_compare_numeric(question_json, answer_data):
    variables = parse_variables(question_json['variables']['$'])
    correct = question_json['expression']['$']
    result = symbolic.compare_numeric(variables, answer_data, correct)
    if 'correct' in result:
        result['status'] = 'correct' if result['correct'] else 'incorrect'
    elif 'error' in result:
        result['status'] = 'error'
    latex = {'latex': symbolic.to_latex(answer_data)}
    result.update(latex)
    return result


register_question_type('compareNumeric', question_check_compare_numeric)
