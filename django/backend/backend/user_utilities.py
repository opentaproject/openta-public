from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import reverse
from django.core.mail import send_mail


def create_activation_link(username):
    token = TimestampSigner().sign(username).split(':', 1)[1]
    return reverse('user-activation-and-reset', kwargs={'username': username, 'token': token})


def send_activation_mail(username, email):
    activate_url = create_activation_link(username)
    send_mail(
        'Account activation',
        activate_url,
        'openta@missopenta.dyndns.org',
        [email],
        fail_silently=False,
    )
