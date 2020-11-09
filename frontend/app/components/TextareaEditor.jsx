import React, { Component} from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import immutable from 'immutable';
import { handleXMLChange } from './AuthorExercise.jsx';
import ReactDOM from 'react-dom';


class TextareaEditor extends Component {
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
    this.myRef = React.createRef();
    //this.state = {
    //  editor: this,
    //}
  }

  handleChange(event) {
    var value = event.target.value
    //console.log("this = ", this)
    //console.log("event = ", event.target )
    //console.log("old value = ", this.state.value)
    //console.log("HANDLE CHANGE FIRED VALUE NEW  = ", value )
    //console.log("onCHANGE PROPS = ", this.props.onChange )
    this.props.onChange( value )
    //event.preventDefault()

  };
 
createMarkup = (value) =>  {
  return {__html: value};
}


  static propTypes = {
    value: PropTypes.string,
    onChange: PropTypes.func,
  };

componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [ { left: "$", right: "$", display: false},
                  { left: "\\[", right: "\\]", display: true},
                  ]
      });
  }


  render(){
    var value = this.props.value;
    var onChange = this.props.onChange;
    var sensitivechars = ['>','$' ]
    var showparsed = false
    if ( value.match(/>|\$|\\]/) ) {
        showparsed = true 
        }
        
    return (
      <div className="uk-panel uk-panel-box uk-margin-small-top  uk-margin-small-right" >
      { showparsed && ( 
        <div className="uk-text-small uk-panel uk-panel-box uk-margin-small-top uk-margin-small-right" dangerouslySetInnerHTML={this.createMarkup( value) }   /> 
      ) }
        <textarea className="uk-width-1-1" value={value} onChange={this.handleChange} /> 
      </div>
    )
  }


}


export default TextareaEditor
