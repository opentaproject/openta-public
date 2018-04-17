import logging
from django.core.signing import TimestampSigner
from django.shortcuts import reverse
from django.template import Context
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage

from utils import send_email_object
from utils import get_localized_template

from course.models import Course

logger = logging.getLogger(__name__)


def create_activation_link(username, reverse_name='user-activation'):
    """Create an activation link for a user.

    Args:
        username:
        reverse_name: Which url to append the activation token to.
            - user-activation (default)
            - user-activation-and-reset (set password at activation)

    Returns:
        The activation url.

    """
    token = TimestampSigner().sign(username).split(':', 1)[1]
    return reverse(reverse_name, kwargs={'username': username, 'token': token})


def send_activation_mail(username, email, reverse_name='user-activation'):
    """Sends an activation email after user registration. 
    
    Args:
        username:
        email:
        reverse_name: Which url to append the activation token to.
            - user-activation (default)
            - user-activation-and-reset (set password at activation)

    Returns:
        Activation url.

    """
    course = Course.objects.first()
    course_url = (
        course.url if course.url is not None else 'https://openta.se/' + course.course_name.lower()
    )
    base_url = course.url if course.url is not None else 'https://openta.se'
    activate_url = create_activation_link(username, reverse_name)
    course_email = Course.objects.course_email()
    template = get_localized_template('mail_activation')
    pcontext = {
        'course_name': 'OpenTA',
        'course_url': 'https://openta.se',
        'username': username,
        'activate_url': base_url + activate_url,
        'course_email': course_email,
    }
    sender = "openta"
    subject = "OpenTA"

    if course is not None:
        sender = course.course_name.lower()
        subject = course.course_long_name
        pcontext.update(
            {
                'course_name': course.course_name,
                'course_long_name': course.course_long_name,
                'course_url': course_url,
            }
        )
    rendered_email = template.render(pcontext)

    email_object = EmailMessage(
        subject=subject + _(" account activation"),
        body=rendered_email,
        from_email=sender + " <" + sender + "@openta.se>",
        to=[email],
        reply_to=[sender + "@openta.se"],
    )
    try:
        n_sent = send_email_object(email_object)
        logger.info("Sent activation mail to email " + email + " (" + str(n_sent) + " delivered)")
    except Exception as e:
        logger.error("Activation email to " + email + " sending failed: " + str(e))
        raise e
    return activate_url
