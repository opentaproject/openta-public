import React from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import QMath from './QMath';
import MathSpan from './MathSpan.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import mathjs from 'mathjs';
import {asciiMathToMathJS} from './mathrender/string_parse.js'


function renderExpression(expression) {
  try {
    var preParsed = asciiMathToMathJS(expression);
    return '$' + mathjs.parse(preParsed.out).toTex() + '$';
  }
  catch(e) {
    return expression;
  }
}


const BaseExerciseRegradeResults = ({activeExercise, exerciseState, regradeAnswers, pending, admin, exerciseKey,pendingState}) => {

  const getQuestionText = key => {
    const q = exerciseState.getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([])).find(q => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['text', '$']);
    }
    return '';
  }

const getQuestionExpression= key => {
    return exerciseState.getIn([activeExercise, 'question',key,'answer'], '')
  }




  const getQuestionType = key => {
    const q = exerciseState.getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([])).find(q => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['@attr', 'type'],'devLinearAlgebra');
    }
    return '';
  }




const timeago = t =>  {
    var txt = moment(t).fromNow('mm')
    txt = txt.replace(/ *ago */,'')
    txt = txt.replace(/ *hours */,' h')
    txt = txt.replace(/ *minutes* */,' m')
    txt = txt.replace(/ a /,' 1 ')
    txt = txt.replace(/ *seconds */,' s')
    txt = txt.replace(/ *a few */,' ~ 0 ')
    txt = txt.replace(/a/,' 1 ')
    return txt 
    }

    


    

  //console.log("pendingState= ", JSON.stringify( pendingState) )
  var txt = JSON.stringify( regradeAnswers, null, 2 )
  //console.log("TXT  = ", txt )
  var progress = pendingState.getIn(['regradeResults'],'99') 
  var pprogress= progress + '%'
  var preview =  pendingState.getIn(['regradePreview','preview'],'NOTHING')
  //console.log("PROGRESS = ", progress)
  console.log("PREVIEW= ", JSON.stringify( preview) )
  console.log("pending = ", pending)
  if (! pending ){
    preview = "Done"
    }
  
  return (
    <div className="uk-panel uk-width-1-1 uk-panel-box uk-margin-top">
        <h3 className="uk-panel-title uk-width-1-1">
          Regrades  {progress}
        </h3>
      { pending && ( 
        <div className="uk-progress uk-width-1-1">
        <div className="uk-progress-bar" style={{'width': pprogress}}><span className="uk-text-bold">{pprogress}</span></div> 
        </div>
            ) }
        <h6 className="uk-width-1-1 uk-overflow-hidden"> {preview} </h6>
      { ! pending && (  
      regradeAnswers.map( (regrade,question) => (
        <div key={"regrade" + question} className="uk-scrollable-box uk-margin-bottom" style={{height:'70vh'}}>
          <div className="uk-align-center"> <QMath  questionType="linearAlgebra" exerciseKey={exerciseKey} expression={getQuestionExpression(question)} />    </div>
          <table className="uk-table">
          <tbody>
          { regrade.map( (answer) => <tr key={answer.get('key')} ><td> <div className="uk-text uk-text-small uk-text-primary"> { answer.get('username').replace(/@[^@]*/,'')
          } </div>  </td>
              <td className="uk-text-small"> {timeago(answer.get('date')) } </td>
          <td className={answer.get('new', false) ? 'uk-text-success' : 'uk-text-danger'} title={answer.get('answer')} data-uk-tooltip>
                             <i className={answer.get('new', false) ? 'uk-icon uk-icon-check uk-text-success' : 'uk-icon uk-icon-close uk-text-danger'} />
                                </td>
 

              <td>    <QMath  questionType="linearAlgebra" exerciseKey={exerciseKey} expression={answer.get('answer')} />    
</td>
              <td> <div className='uk-text uk-text-small'> {answer.get('answer')} </div> </td>
               
              </tr> ) }
          </tbody>
          </table>
    </div>
  ))  ) }
  </div>
  )
}

const mapStateToProps = state => {
  var activeExercise = state.get('activeExercise');
  return ({
    regradeAnswers: state.getIn(['results', 'exercises', activeExercise, 'regrade'] , immutable.Map({})),
    pending: state.getIn(['pendingState', 'regradeResults'], false),
    pendingState: state.getIn(['pendingState'],immutable.Map({}) ),
    activeExercise: activeExercise,
    exerciseState: state.get('exerciseState'),
    exerciseKey: state.get('activeExercise'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  });
}

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseRegradeResults)
