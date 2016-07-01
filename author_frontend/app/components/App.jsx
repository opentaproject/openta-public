import React from 'react';
import Counter from './Counter';
import ExerciseList from './ExerciseList';
import Exercise from './Exercise';

export default class App extends React.Component {
  render() {
    return (
      <div id="content" className="uk-container uk-grid">
        <ExerciseList />
        <Exercise />
      </div>
    );
  }
}
