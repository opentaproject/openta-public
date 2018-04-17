import React, { Component } from 'react';
import uniqueId from 'lodash/uniqueId';

export default class HelpNumeric extends Component {
  render = () => (
  <span>
<a data-uk-toggle={"{target:'#" + this.id + "'}"}><i className="uk-icon uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a>
<div id={this.id} className="uk-hidden">
  <hr/>
  <p>Skriv in ditt svar i rutan och tryck på <i className="uk-icon uk-icon-send uk-margin-small-left uk-margin-small-right"/> för att kontrollera</p>
  <p>
I svarsfältet kan man bara ange ett numerisk svar med enheter.
  </p>
  <hr/>
</div>
  </span>
);

  componentWillMount = () => {
    this.id = uniqueId('help');
  } 
}
