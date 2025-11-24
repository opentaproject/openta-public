// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { useState } from 'react';
import { jsonfetch } from '../fetch_backend.js';

const BugReport = ({username,subdomain, admin }) => {
  const [message, setMessage] = useState('');
  const [subject , setSubject] = useState('');
  const [sending, setSending] = useState(false);

  const openModal = () => {
    try {
      UIkit.modal('#bug-report-modal').show();
    } catch (e) {
      // fallback: anchor-based open if UIkit not available
      const el = document.getElementById('bug-report-modal');
      if (el) el.style.display = 'block';
    }
  };

  const closeModal = () => {
    try {
      UIkit.modal('#bug-report-modal').hide();
    } catch (e) {
      const el = document.getElementById('bug-report-modal');
      if (el) el.style.display = 'none';
    }
  };
 
  var s = username
  const onSend = async () => {
    var s = 'user: ' + username  + ', course: ' + subdomain + ', admin: ' + admin
    if (!message.trim()) {
      try {
        UIkit.notify( s,  { status: 'warning', timeout: 3000 });
      } catch (_) {}
      return;
    }
    setSending(true);
    try {
      const payload = {
        message: message,
	subject : subject,
        url: window.location ? window.location.href : '',
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : ''
      };
      const res = await jsonfetch('/bug_report/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.status >= 200 && res.status < 300) {
        try {
          UIkit.notify('Bug report sent. Check your course email!', { status: 'success', timeout: 4000 });
        } catch (_) {}
        setMessage('');
	setSubject('');
        closeModal();
      } else {
        const txt = await res.text();
        throw new Error(txt || 'Failed to send bug report');
      }
    } catch (err) {
      try {
        UIkit.notify('Could not send bug report.', { status: 'danger', timeout: 5000 });
      } catch (_) {}
      // keep modal open to let user retry
    } finally {
      setSending(false);
    }
  };

  var s = 'Report a bug; if relevant which exercise; provide detail'
  return (
    <span>
      <button className="uk-button uk-text-danger uk-button-link" onClick={openModal} title="Report a bug. You will get email; do a ReplyToAll all there if you need more space.">
        <i className="uk-icon uk-icon-bug" />
      </button>

      <div id="bug-report-modal" className="uk-modal">
        <div className="uk-modal-dialog" style={{ maxWidth: '600px' }}>
          <a className="uk-modal-close uk-close" />
          <h3 className="uk-margin-small-bottom">Report a bug.</h3>

          <textarea
            className="uk-width-1-1"
            rows={2}
            placeholder="Subject" 
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={sending}
          />
	  <p/>
          <textarea
            className="uk-width-1-1"
            rows={8}
            placeholder="Message:  An email will be sent to your course email. Reply to all there if you need more space to describe the bug.  " 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={sending}
          />


          <div className="uk-margin-top uk-text-right">
            <button className="uk-button" onClick={closeModal} disabled={sending}>
              Cancel
            </button>
            <button
              className="uk-button uk-button-primary uk-margin-left"
              onClick={onSend}
              disabled={sending}
            >
              {sending ? 'Sending…' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </span>
  );
};

export default BugReport;

