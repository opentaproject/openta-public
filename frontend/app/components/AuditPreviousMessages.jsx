import React, { Component } from 'react';

const AuditPreviousMessages = ({auditsList, onOldMessageClick, activeAudit, confirm}) =>
    (
      <div className="uk-panel uk-panel-box uk-margin-small-top">
        <h3 className="uk-panel-title">Other messages</h3>
        <div className="uk-scrollable-box">
          <table className="uk-table uk-table-hover">
            <tbody>
              { auditsList.reverse().filter( audit => /*audit.get('sent') &&*/ audit.get('message','').length > 0)
                          .groupBy( audit => audit.get('message') )
                          .map( group => group.first() )
                          .map( audit => (
                            <tr key={audit.get('pk')} >
                              <td>
                                <div className="uk-flex uk-flex-column uk-flex-middle">
                                    <div>
                                        {confirm && <a onClick={() => UIkit.modal.confirm('Replace current text with this message?', () => onOldMessageClick(activeAudit, audit.get('message')))}>Use</a>}
                                        {!confirm && <a onClick={() => onOldMessageClick(activeAudit, audit.get('message'))}>Use</a>}
                                    </div>
                                  <div>
                                    { audit.get('message') }
                                  </div>
                                </div>
                              </td>
                            </tr>
                          ))
                          .toList() }
            </tbody>
          </table>
        </div>
      </div>
    );

export default AuditPreviousMessages;
