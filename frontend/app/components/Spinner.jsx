import React, { Component } from 'react';

const Spinner = ({icon='uk-icon-cog', size='uk-icon-large', spin='uk-icon-spin', className="", title=''}) => {
  return (<i title={title} className={icon + " " + spin + " " + size + " Spinner " + className}></i>)
};

export default Spinner
