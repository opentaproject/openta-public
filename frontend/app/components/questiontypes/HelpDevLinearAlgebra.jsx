import React, { Component } from 'react';
import T from "../Translation.jsx";
import uniqueId from 'lodash/uniqueId';
import MathSpan from '../MathSpan'
import PropTypes from 'prop-types'
import t from '../../translations.js';
import DOMPurify from 'dompurify';


export default class HelpDevLinearAlgebra extends Component {
  constructor() {
        super();
  }
static PropTypes = {
    msg: PropTypes.string,
    }

render() {
  var style='uk-icon uk-text-danger  uk-icon-small uk-icon-question-circle-o uk-margin-small-left'
  var substyle = 'uk-hidden uk-text-warning uk-text-small'
  if( this.props.msg ){
       // console.log("msg = ", this.props.msg )
        var msg = this.props.msg
        if ( msg == 'Syntax OK' ){
            style='uk-icon  uk-text-success uk-icon-small uk-icon-question-circle-o uk-margin-small-left'
            var substyle = 'uk-hidden uk-text-warning uk-text-small' // TRIED TO CHANGE THIS BUT THIS CLOSES THE QUESITON BOX AND IS IRRITATINT
        }

    return ( 

        <span> <a data-uk-toggle={"{target:'#" + this.id + "'}"}>
        <i className={style}/></a>
         <div id={this.id} className={substyle}> {msg} </div> 
    </span>

)







  } else {


return (

  <span> <a data-uk-toggle={"{target:'#" + this.id + "'}"}><i className="uk-icon uk-text-success uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a> 

<div id={this.id} className="uk-hidden"> 

 <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize( t('Press send to check') )}} />



</div> </span>

) }
  }
//const mapStateToProps = (state) => {
//  const defaultLanguage = state.getIn(['course', 'languages', 0], 'en')
//    return {
//      language: state.get('lang', defaultLanguage)
//    };
//}

// export default (mapStateToProps)(HelpDevLinearAlgebra);

componentWillMount = () => {
    this.id = uniqueId('help');
  } 
}


