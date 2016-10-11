from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import reverse
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from course.models import Course
from django.template.loader import get_template
from django.template import Context


def create_activation_link(username, reverse_name='user-activation'):
    token = TimestampSigner().sign(username).split(':', 1)[1]
    return reverse(reverse_name, kwargs={'username': username, 'token': token})


def send_activation_mail(username, email, reverse_name='user-activation'):
    activate_url = create_activation_link(username, reverse_name)
    template = get_template('mail_activation')
    pcontext = {
        'course_name': 'OpenTA',
        'course_url': 'https://openta.se',
        'username': username,
        'activate_url': 'https://openta.se' + activate_url,
    }
    sender = "openta"
    try:
        course = Course.objects.first()
        sender = course.course_name.lower()
        pcontext.update(
            {
                'course_name': course.course_name,
                'course_url': 'https://openta.se/' + course.course_name.lower(),
            }
        )
    except ObjectDoesNotExist:
        pass
    context = Context(pcontext)
    rendered_email = template.render(context)
    send_mail(
        'Account activation', rendered_email, sender + '@openta.se', [email], fail_silently=False
    )
    return activate_url
