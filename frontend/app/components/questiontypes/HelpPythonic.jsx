import React, { Component } from 'react';
import uniqueId from 'lodash/uniqueId';
import HelpCompareNumeric from './HelpCompareNumeric.jsx'
import MathSpan from '../MathSpan'
import t from '../../translations.js';
import DOMPurify from 'dompurify';

export default class HelpLinearAlgebra extends Component {
  render = () => (
  <span>
<a data-uk-toggle={"{target:'#" + this.id + "'}"}><i className="uk-icon uk-text-warning uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a>
<div id={this.id} className="uk-hidden">
      <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize( t('choose your language at the top') )}} />
</div>
</span>
);

  componentWillMount = () => {
    this.id = uniqueId('help');
  } 
}
