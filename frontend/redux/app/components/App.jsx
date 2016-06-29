import React from 'react';
import Counter from './Counter';
import Exercises from './Exercises';

export default class App extends React.Component {
  render() {
    return (
      <div id="content" className="uk-container uk-grid">
        <h1>&nbsp;</h1>
        {/*<Counter />*/}
        <Exercises />
        <Exercise />
      </div>
    );
  }
}
