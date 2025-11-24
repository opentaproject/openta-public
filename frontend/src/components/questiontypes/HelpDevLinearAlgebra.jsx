import React, { Component } from 'react';
import uniqueId from 'lodash/uniqueId';
import PropTypes from 'prop-types';

export default class HelpDevLinearAlgebra extends Component {
  constructor() {
    super();
  }
  static propTypes = {
    msg: PropTypes.object
  };

  render() {
    var style = 'uk-icon uk-text-danger  uk-icon-small uk-icon-question-circle-o uk-margin-small-left';
    var substyle = 'uk-hidden uk-text-warning uk-text-small';
    if (this.props.msg) {
      var msg = this.props.msg;
    } else {
      var msg = 'Press send to check';
    }
    if (msg == 'Syntax OK') {
      style = 'uk-icon  uk-text-success uk-icon-small uk-icon-question-circle-o uk-margin-small-left';
      var substyle = 'uk-hidden uk-text-warning uk-text-small'; // TRIED TO CHANGE THIS BUT THIS CLOSES THE QUESITON BOX AND IS IRRITATINT
    }
    return (
      <span>
        {' '}
        <a data-uk-toggle={"{target:'#" + this.id + "'}"}>
          <i className={style} />
        </a>
        <div id={this.id} className={substyle}>
          {' '}
          {msg}{' '}
        </div>
      </span>
    );
  }

  UNSAFE_componentWillMount = () => {
    this.id = uniqueId('help');
  };
}
