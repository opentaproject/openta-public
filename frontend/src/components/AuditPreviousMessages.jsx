// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
var unstableKey = 437;
const nextUnstableKey = () => unstableKey++;

const stringlist = (auditsList) => {
  var lis = auditsList.map((audit) => audit.get('message', ''));
  var res = lis.reduce(function (acc, curr) {
    return acc[curr] ? ++acc[curr] : (acc[curr] = 1), acc;
  }, {});
  var set = new Set(lis);
  var strings = Array.from(set);
  //console.log("res = ", res )
  var sorted = strings.sort(function (a, b) {
    //console.log("a[1] = ", res[a], "res[b] = ", res[b] )
    if (res[a] < res[b]) {
      return 1;
    } else if (res[a] > res[b]) {
      return -1;
    } else {
      return 0;
    }
  });
  var newlist = sorted.map((s) => auditsList.find((a) => a.get('message', '') == s));
  var newsorted = newlist.map((a) => ({
    message: a.get('message', ''),
    points: a.get('points'),
    revision_needed: a.get('revision_needed')
  }));
  var newsorted = newsorted.filter((a) => a['points'] !== '');
  return newsorted;
};

const AuditPreviousMessages = ({ auditsList, onOldMessageClick, activeAudit, confirm }) => {
  var adata = stringlist(auditsList);
  //console.log(" stringlist = ",  adata)
  return (
    <div className="uk-panel uk-panel-box uk-margin-small-top">
      <h3 className="uk-panel-title">Other messages</h3>
      <div className="uk-scrollable-box">
        <table className="uk-table uk-table-hover">
          <tbody>
            {adata.map((a) => (
              <tr key={nextUnstableKey()}>
                <td>
                  <div className={'uk-flex uk-flex-column uk-flex-left '}>
                    <a
                      className={a.revision_needed ? 'uk-text-danger' : 'uk-text-success'}
                      onClick={() => onOldMessageClick(activeAudit, a.message, a.points, a.revision_needed)}
                    >
                      {' '}
                      {a.points + '-p: ' + a.message}{' '}
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditPreviousMessages;
