import React, { Component } from 'react';
import TextareaAutosize  from 'react-textarea-autosize';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { uploadAsset } from '../fetchers/assets.js';
import { getcookie } from '../cookies';

var CSRF_TOKEN_NAME = getcookie('csrf_cookie_name') ? getcookie('csrf_cookie_name')[0] : 'csrftoken'; // Duplicate CSRF tokens if several sites
var CSRF_TOKEN = getcookie(CSRF_TOKEN_NAME)[0];

class SafeTextarea extends Component {

  constructor(props) {
    super(props);
    this.myRef = React.createRef();
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleSaveAs = this.handleSaveAs.bind(this);
    this.handleReset = this.handleReset.bind(this);
    var [, , exerciseKey, , filename] = this.props.src.split('/');
    this.state =  { filename: filename, exerciseKey: exerciseKey , error: false , tex : '', texinitial: '' }
    fetch(this.props.src, { cache: 'no-cache' })
      .then((response) => {
        return response.text();
      })
      .then((data) => {
        this.setState({ tex: data , texinitial: data });
      });
  }

  static propTypes = {
    src: PropTypes.string,
    close: PropTypes.func,
  };

  onError = (event) => {
    this.setState({ error: true });
  };

  handleChange(event) {
    this.setState({ tex: event.target.value });
  }

  handleReset(event,texinitial) {
    this.setState({ tex: texinitial });
  }

  handleSaveAs(event,newfile) {
    this.setState({ filename: newfile });
  }


  handleSubmit = (event) =>  {
    event.preventDefault();
    var f = new File([this.state.tex], this.state.filename, { type: 'text/plain' });
    this.props.doUpload(this.state.exerciseKey, f);
  }

  render() {
    var token = CSRF_TOKEN;
    var texin = this.state.texinitial
    return (
      <div className="uk-panel">
        <div className="uk-width-1-1 uk-badge-secondary uk-panel-badge uk-badge">
          <form onSubmit={  (event) => this.handleSubmit(event)} method="post" style={{ display: 'inline' }}>
	<div className="uk-text uk-text-large" style={{ resize: 'both' }} > Editing {this.state.filename} </div>
            <input type="hidden" name="csrfmiddlewaretoken" value={token} />
            <TextareaAutosize
              rows="20"
              className="uk-width-1-1 uk-textarea"
              type="text"
	      value={this.state.tex}
              onChange={this.handleChange}
            />
            <span>
              <input type="submit" value="Save" />
              <button onClick={() => this.props.close()}> Close </button>
            </span>
	    </form>
	  <button  onClick={(event) => UIkit.modal.prompt('Rename when saving as ',this.state.filename , ( newvalue ) => {
		event.preventDefault();
	        this.setState({filename: newvalue});
	      	 } ) }> Rename </button>
	   <button  className={"uk-button-danger"} onClick={() =>   {
		  this.handleReset(event, texin) } } > Reset </button>

        </div>
      </div>
    )
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    doUpload: (exerciseKey, f) => dispatch(uploadAsset(exerciseKey, f)).catch((err) => console.log(err)),
  };
};

export default connect(null, mapDispatchToProps)(SafeTextarea);
