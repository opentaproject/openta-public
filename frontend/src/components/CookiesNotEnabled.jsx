// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import Alert from './Alert';

const Spinner = ({ help_url = '' }) => {
  console.log(' SPINNER ', help_url);
  if (help_url == '') {
    return (
      <div id="content" className="uk-width-1-1">
        <div id="main" className="uk-grid uk-margin-remove">
          <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
            <Alert>
              Please enable cookies (and third-party cookies) to access OpenTA. If you are using Canvas or Moodle on a
              mobile device, use the Canvas or Moodle app instead of a browser.
            </Alert>
          </div>
        </div>
      </div>
    );
  } else {
    return (
      <div id="content" className="uk-width-1-1">
        <div id="main" className="uk-grid uk-margin-remove">
          <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
            <Alert>
              {' '}
              You need to allow canvas to use third party cookies. on Safari: Uncheck Prevent cross-site tracking. on
              Chrome: Preferences -> Privacy and security -> Cookies and other site data -> Sites that can always use
              cookies -> Add -> \[*.]instructure.com on Firefox: Preferences -> Privacy and security -> Cookies and
              other site data -> Manage Exception .. Add chalmers.instructure.com and allow and Save. If you are using
              OpenTA on a mobile device, use the Canvas or Moodle app.
              <a href={help_url}> Click here for further help: </a>{' '}
            </Alert>
          </div>
        </div>
      </div>
    );
  }
};

export default Spinner;
