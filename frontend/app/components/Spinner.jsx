import React, { PropTypes, Component } from 'react';

const Spinner = ({icon='uk-icon-cog', size='uk-icon-large', spin='uk-icon-spin', className=""}) => {
  return (<i className={icon + " " + spin + " " + size + " " + className}></i>)
};

export default Spinner
