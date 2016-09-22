from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import reverse
from django.core.mail import send_mail


def create_activation_link(username, reverse_name='user-activation'):
    token = TimestampSigner().sign(username).split(':', 1)[1]
    return reverse(reverse_name, kwargs={'username': username, 'token': token})


def send_activation_mail(username, email, reverse_name='user-activation'):
    activate_url = create_activation_link(username, reverse_name)
    send_mail(
        'Account activation',
        activate_url,
        'openta@missopenta.dyndns.org',
        [email],
        fail_silently=False,
    )
