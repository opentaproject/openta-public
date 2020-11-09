import React, { Component } from 'react';
import T from "../Translation.jsx";
import uniqueId from 'lodash/uniqueId';
import MathSpan from '../MathSpan'
import PropTypes from 'prop-types'
import t from '../../translations.js';
import DOMPurify from 'dompurify';
import ReactDOM from 'react-dom';


export default class HelpDevLinearAlgebra extends Component {
  constructor() {
        var id = ''
        super();
  }
static propTypes = {
    msg: PropTypes.string,
    }

render() {
if ( this.props.msg && !( this.props.msg == 'Syntax OK' ) ){
    var style='uk-icon uk-text-danger  uk-icon-small uk-icon-question-circle-o uk-margin-small-left'
    var badge_style = 'uk-badge uk-badge-danger'
    var msg = this.props.msg 
    } else {
    var  style='uk-icon uk-text-success uk-icon-small uk-icon-question-circle-o uk-margin-small-left'
    var badge_style = 'uk-badge uk-badge-success'
    var msg = 'Syntax OK'
    }
var dom = (<span>
<a data-uk-toggle={"{target:'#" + this.id + "'}"}><i className={style} /></a>
<div id={this.id} className="uk-hidden">


<span className={badge_style} dangerouslySetInnerHTML={{__html: DOMPurify.sanitize( msg )}} />

</div>
  </span>
);


return dom 
}

componentWillMount = () => {
   this.id = uniqueId('help');
  } 

}
