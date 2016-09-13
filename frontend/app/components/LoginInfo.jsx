import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import {
  updateActiveAdminTool
} from '../actions.js';

import immutable from 'immutable';

const BaseLoginInfo = ({ username, admin, activeExercise, activeAdminTool, onXMLEditorClick, onOptionsClick}) => {
  var admintoolsmenu = [
    {
      id: 'xml-editor',
      name: 'XML Editor',
      callback: onXMLEditorClick
    },
    {
      id: 'options',
      name: 'Options',
      callback: onOptionsClick
    }
  ];
  var items = admintoolsmenu.map( item => {
    var cssclass = "uk-button uk-button-primary" + (activeAdminTool === item.id ? " uk-active" : "");
    return ( <a className={cssclass} onClick={item.callback}>{item.name}</a> );
  });
  var admintools = (
    <div className="uk-button-group uk-margin-left">
      {items}
    </div>
  );
return (
  <nav id="login" className="uk-nav uk-navbar-attached ta-nav border-bottom">
  <div className="uk-container uk-container-center">
  <div className="uk-navbar-brand"><i className="uk-icon uk-icon-medium uk-icon-circle-o"></i><span className="uk-text-small uk-text-middle"> OpenTA</span></div>
  <div className="uk-navbar-flip">
  <ul className="uk-navbar-nav">
      <li>
      <a href="/logout/?next=/login"><i className="uk-icon uk-icon-sign-out uk-text-large uk-text-middle"></i></a>
      </li>
  </ul>
  </div>
  <div className="uk-navbar-content uk-navbar-center">
    <i className={"uk-icon uk-text-success " + (admin ? "uk-icon-user-md" : "uk-icon-user")}></i> <span className="uk-text-large uk-text-middle">{username}</span>{ admin ? ( <span className="uk-text-small uk-text-middle"> (admin)</span> ) : "" }
  { admin && activeExercise && admintools }
</div>
  </div>
  </nav>
);
}

BaseLoginInfo.propTypes = {
  username: PropTypes.string,
  admin: PropTypes.bool,
  activeExercise: PropTypes.string,
  activeAdminTool: PropTypes.string,
  onXMLEditorClick: PropTypes.func,
  onOptionsClick: PropTypes.func
};

const mapStateToProps = state => {
  return ({
  username: state.getIn(['login', 'username']),
  admin: state.getIn(['login', 'admin']),
  activeExercise: state.get('activeExercise'),
  activeAdminTool: state.get('activeAdminTool')
});
}

const mapDispatchToProps = dispatch => ({
  onXMLEditorClick: (event) => dispatch(updateActiveAdminTool('xml-editor')),
    onOptionsClick: (event) => dispatch(updateActiveAdminTool('options')),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseLoginInfo)
