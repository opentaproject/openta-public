import React from 'react';
// See  https://github.com/savalanpour/react-component-countdown-timer/blob/master/src/lib/index.jsx
const Spinner = ({
  icon = 'uk-icon-cog',
  size = 'uk-icon-large',
  spin = 'uk-icon-spin',
  className = '',
  title = '',
  msg = ''
}) => {
  return (
    <span>
      {' '}
      <i title={title} className={icon + ' ' + spin + ' ' + size + ' Spinner ' + className}></i>
      <div className={className + 'uk-button'} >{msg}</div>
    </span>
  );
};

export default Spinner;
