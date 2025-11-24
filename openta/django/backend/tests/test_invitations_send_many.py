# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from invitations.utils import get_invitation_model


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
def test_send_many_invites_json_creates_invites_and_sets_from_email(client):
    Invitation = get_invitation_model()

    inviter = User.objects.create_user(username='inviter', email='inviter@example.com', password='pw')
    client.force_login(inviter)

    url = reverse('invitations:send-many-invites')
    payload = {"emails": ["alice@example.com", "bob@example.com"], "role": "3"}
    resp = client.post(url, data=json.dumps(payload), content_type='application/json')
    print('JSON status:', resp.status_code)
    print('JSON body:', resp.content)
    assert resp.status_code in (200, 201)

    invites = Invitation.objects.filter(email__in=["alice@example.com", "bob@example.com"]) \
        .order_by('email')
    assert invites.count() == 2
    for inv in invites:
        assert inv.inviter_id == inviter.id
        assert inv.key.startswith('3')

    # Emails captured by locmem backend
    assert len(mail.outbox) >= 2
    from_emails = {m.from_email for m in mail.outbox}
    assert from_emails == {inviter.email}


@pytest.mark.django_db
@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
def test_send_many_invites_form_page(client):
    inviter = User.objects.create_user(username='inviter2', email='inviter2@example.com', password='pw')
    client.force_login(inviter)

    # GET shows form
    url = reverse('invitations:send-many-form')
    resp = client.get(url)
    print('FORM GET status:', resp.status_code)
    assert resp.status_code == 200
    assert b'mail' in resp.content

    # POST creates invitations
    form_data = {
        'emails': 'carol@example.com, dave@example.com',
        'role': '1',
    }
    resp2 = client.post(url, data=form_data)
    print('FORM POST status:', resp2.status_code)
    print('FORM POST body:', resp2.content)
    assert resp2.status_code == 200

    Invitation = get_invitation_model()
    invites = Invitation.objects.filter(email__in=["carol@example.com", "dave@example.com"]).order_by('email')
    assert invites.count() == 2
    for inv in invites:
        assert inv.inviter_id == inviter.id
        assert inv.key.startswith('1')
