import React from 'react';
import { connect } from 'react-redux';
import {
  fetchRegradeTask,
  fetchExerciseRegradeResults,
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

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;



function renderExpression(expression) {
  try {
    var preParsed = asciiMathToMathJS(expression);
    return '$' + mathjs.parse(preParsed.out).toTex() + '$';
  }
  catch(e) {
    return expression;
  }
}


const BaseExerciseRegradeResults = ({activeExercise, exerciseState, regradeAnswers, pending, admin, exerciseKey,progress,preview,on_accept_regrade,regrade}) => {

  const getQuestionText = key => {
    const q = exerciseState.getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([])).find(q => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['text', '$']);
    }
    return '';
  }

const getQuestionExpression= key => {
    //console.log("GET QUESTION EXPRESSIN key = ", key )
    //console.log("ACTIVE EXERCISE = ", activeExercise)
    //console.log("DATA = ",  exerciseState.getIn([activeExercise ]  ) )
    var res = exerciseState.getIn([activeExercise, 'question',key,'answer'], 'Click submit to see correct answer')
    //console.log("RES = ", res )
    return res
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

    


    

  var txt = JSON.stringify( regradeAnswers, null, 2 )
  var pprogress= progress + '%'
  var detail = ( preview == 'Cancelled' ||  preview == 'Done' || preview == 'Old Regrade')  ? preview : ''
  var lines =  preview.split('\n') 
  lines.shift()
  var finished = ( pending == 'finished' )
  var show_accept_and_reject = (  preview == 'Done' || preview == 'Old Regrade' ) && ( ! finished )
  var show_reject_only = ( preview == 'Cancelled')  && ( ! finished )
  var show_accept_reject = ( ! ( detail == '' ) ) || ( preview == '' ) && ( ! finished )
  var ekey = String( exerciseKey)
  var waiting = ( progress == 0 )  && ( ! show_accept_reject )
  show_reject_only = ( show_reject_only  || preview == 'Done' ) && ( ! finished)
  return (
    <div className="uk-panel uk-width-1-1 uk-panel-box uk-margin-top">
        <h4 className="uk-panel-title uk-width-1-1">
        { ( true || ( show_reject_only  &&  ! show_accept_and_reject )  ) && (
        <button   className="uk-button uk-button-danger"  onClick={ () => on_accept_regrade( ekey , 'reset') }> Reset </button>
        ) }
        <button  className="uk-button uk-button-primary" onClick={ () => regrade() }>  Regrade </button> 
          { ! show_accept_reject && (
          <button  className="uk-button uk-button-danger" onClick={ () => on_accept_regrade( ekey , 'cancel') }>  Cancel </button>
          
          ) }
        </h4>
        <h4>
        
        {waiting && ( <button className='uk-button '> Waiting </button> ) }
      {! pending  && (
        <div>
      <button  className="uk-button uk-button-success" onClick={ () => on_accept_regrade( ekey , 'yes') }>  Accept </button>
      <button  className="uk-button uk-button-danger" onClick={ () => on_accept_regrade( ekey , 'no') }>  Reject </button>
        </div>
        ) }
      </h4>
      { pending && ( 
        <div className="uk-progress uk-width-1-1">
        <div className="uk-progress-bar" style={{'width': pprogress}}><span className="uk-text-bold">{pprogress}</span></div> 
        </div>
      )}
      { pending && (
        <div>
            
         <h6 className="uk-width-1-1 uk-overflow-hidden"><table><tbody>{ lines.map( ( line ) => ( <tr key={'lis' + nextUnstableKey() }><td className='uk-overflow-hidden'>  {line}  </td> </tr>  ) ) }</tbody></table>
           </h6> 
        </div>
        ) }
      { true && (
      regradeAnswers.map( (regrade,question) => (
        <div key={"regrade" + question} className="uk-scrollable-box uk-margin-bottom" style={{height:'70vh'}}>
          <div className="uk-align-center"> <QMath  questionType="devLinearAlgebra" exerciseKey={exerciseKey} expression={getQuestionExpression(question)} />   </div>
          <table className="uk-table">
          <tbody>
          { regrade.map( (answer) => <tr key={answer.get('key')} ><td> <div className="uk-text uk-text-small uk-text-primary"> { answer.get('username').replace(/@[^@]*/,'')
          } </div>  </td>
              <td className="uk-text-small"> {timeago(answer.get('date')) } </td>
          <td className={answer.get('new', false) ? 'uk-text-success' : 'uk-text-danger'} title={answer.get('answer')} data-uk-tooltip>  {answer.get('old') ? 'ok' : 'nok' } -> { answer.get('new') ? 'ok' : 'nok' }  
                             <i className={answer.get('new', false) ? 'uk-icon uk-icon-check uk-text-success' : 'uk-icon uk-icon-close uk-text-danger'} />
                                </td>
 

              <td>    <QMath  questionType="linearAlgebra" exerciseKey={exerciseKey} expression={answer.get('answer')} />    
</td>
              <td> <div className='uk-text uk-text-small'> {answer.get('answer')} </div> </td> <td> {answer.get('error','') } </td>
               
              </tr> ) }
          </tbody>
          </table>
    </div>
  ))  ) }
  </div>
  )
}

const mapDispatchToProps = dispatch => ({
 on_accept_regrade :  ( exercise, yesno ) => dispatch( fetchRegradeTask(exercise,yesno) ),
 regrade:  ( exercise) => dispatch( fetchExerciseRegradeResults() )
})

const mapStateToProps = state => {
  var activeExercise = state.get('activeExercise');
  return ({
    preview : state.getIn(['pendingState','regradePreview',activeExercise,'preview'],''),
    regradeAnswers: state.getIn(['results', 'exercises', activeExercise, 'regrade'] , immutable.Map({})),
    pending: state.getIn(['pendingState', 'regradeResults',activeExercise], false),
    progress: state.getIn(['pendingState','regradeResults',activeExercise],'99') ,
    pendingState: state.getIn(['pendingState'],immutable.Map({}) ),
    activeExercise: activeExercise,
    exerciseState: state.get('exerciseState'),
    exerciseKey: state.get('activeExercise'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  });
}


export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseRegradeResults)
