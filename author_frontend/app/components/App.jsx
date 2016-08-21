import React from 'react';
import Counter from './Counter';
import ExerciseList from './ExerciseList';
import Exercise from './Exercise';
import AuthorExercise from './AuthorExercise';
import LoginInfo from './LoginInfo';

export default class App extends React.Component {
  render() {
    return (
      <div>
      <LoginInfo/>
      <div id="content" className="uk-container uk-container-center">
        <div id="main" className="uk-grid">
          <ExerciseList />
          <div className="uk-width-medium-5-6">
            <AuthorExercise />
          </div>
        </div>
      </div>
      </div>
    );
  }
}
