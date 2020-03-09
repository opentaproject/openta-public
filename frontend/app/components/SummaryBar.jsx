import React, { Component} from 'react';
import { connect } from "react-redux";
import { navigateMenuArray } from "../menu.js";
import T from "./Translation.jsx";
import t from "../translations.js";
import LoginInfo from "./LoginInfo.jsx"
import Cookies from 'universal-cookie';


import immutable from "immutable";
import moment from "moment";
import { SUBPATH } from "../settings.js";
import {
  updateExerciseFilter
} from '../actions.js';
import {
    fetchExerciseTree,
} from '../fetchers.js';



class BaseSummaryBar extends Component  {
//{ student, exerciseState, onHome, author,
//  displaystyle, iframed, course, show_home, username,
//  onExerciseFilterChange, activeCourse, exercisefilter }
  constructor() {
    super();
   this.state = {'exercisefilter' : {
            'required_exercises' : true, 
            'optional_exercises': true, 
            'bonus_exercises': true, 
            'unpublished_exercises': true,
            }
    }
   this.handleToggle = this.handleToggle.bind(this)

  }


  componentDidMount(props,state,root ){
    this.setState({'exercisefilter' : this.props.exercisefilter } )
    }
  


  handleToggle(exercisefilter, filter_toggle,activeCourse) {
    var newfilter = this.props.exercisefilter
    newfilter[filter_toggle] = ! newfilter[filter_toggle]
    this.setState({'exercisefilter' :  newfilter} )
    this.props.onExerciseFilterChange( newfilter , activeCourse )
    var cookies = new Cookies()
    var clist = []
    for ( var entry in newfilter  ){
        if( newfilter[entry] && entry !== 'undefined' && entry !== '' ){
          clist.push( entry )
          }
        }
    cookies.set('exercisefilter',  clist.join(';') ,{path : '/'} )


    }

  render () {
  var show_edit_toggle = this.props.show_edit_toggle
  var exercisefilter = this.props.exercisefilter;
  var summary = this.props.exerciseState.getIn(['summary'],'SUMMARY MISSING')
  var sums =  this.props.exerciseState.getIn(['sums'], immutable.List( []) )
  var sum01 = sums.getIn(['required','feedback','number_complete_by_deadline'],0)
  var sum02 = sums.getIn(['required','feedback','number_complete'],0) - sum01
  var sum03 = sums.getIn(['required','nofeedback','number_complete_by_deadline'],0)
  var sum04 = sums.getIn(['required','nofeedback','number_complete'],0) - sum03

  var sum11 = sums.getIn(['bonus','feedback','number_complete_by_deadline'],0)
  var sum12 = sums.getIn(['bonus','feedback','number_complete'],0) - sum11 
  var sum13 = sums.getIn(['bonus','nofeedback','number_complete_by_deadline'],0)
  var sum14 = sums.getIn(['bonus','nofeedback','number_complete'],0) - sum13

  
  var sum21 = sums.getIn(['optional','feedback','number_complete_by_deadline'],0)
  var sum22 = sums.getIn(['optional','feedback','number_complete'],0) - sum21
  var sum23 = sums.getIn(['optional','nofeedback','number_complete_by_deadline'],0)
  var sum24 = sums.getIn(['optional','nofeedback','number_complete'],0) - sum23

  var mess0 =   ( "Required: " + sum01  + " correct and ontime " )
  mess0 = mess0 + ( ( 0 !== sum02  )   ? ( ", " + sum02 + "correct but late " ) : ''    )
  mess0 = mess0 + ( ( 0 !== sum03  )   ? ( ", " + sum03 + " unchecked ontime " ) : ''   )
  mess0 = mess0 + (  ( 0 !== sum04  )   ? ( ", " + sum04 + " unchecked late " ) : ''   )

  
  var mess1 =   ( "Bonus: " + sum11  + " correct and ontime " ) 
  mess1 = mess1 + ( ( 0 !== sum12  )   ? ( ", " + sum12 + "correct but late " ) : ''    )
  mess1 = mess1 + ( ( 0 !== sum13  )   ? ( ", " + sum13 + " unchecked ontime " ) : ''   )
  mess1 = mess1 + (  ( 0 !== sum14  )   ? ( ", " + sum14 + " unchecked late " ) : ''   )

  
  var mess2 =    ( "Optional: " + sum21  + " correct and ontime " ) 
  mess2 = mess2 + ( ( 0 !== sum22  )   ? ( ", " + sum22 + "correct but late " ) : ''    )
  mess2 = mess2 + ( ( 0 !== sum23  )   ? ( ", " + sum23 + " unchecked ontime " ) : ''   )
  mess2 = mess2 + (  ( 0 !== sum24  )   ? ( ", " + sum24 + " unchecked late " ) : ''   )
 
 var level = 0
 var use_header = true
 var runtests = this.props.exerciseState.getIn(['runtests'] ,false)
 var force_all_header_buttons = true
 var author = this.props.author
 var username = this.props.username

  
 var show_obligatory =   true == ( ( sum01 + sum03 > 2 )  | author | runtests | force_all_header_buttons)
 var show_bonus =  true == ( ( sum11 + sum13 > 2 )  | author  | runtests| force_all_header_buttons)
 var show_optional = true == ( ( sum21 + sum23 > 2 ) | author | runtests| force_all_header_buttons)
 var show_listview = true == ( ( true == ( show_obligatory | show_bonus | show_optional ) ) | author | runtests| force_all_header_buttons)
 var show_logininfo_button = true == (  author | runtests )
 var show_logininfo = true == ( ( true ==  ( sum11 + sum13 + sum01 + sum03 + sum21 + sum23 ) > 2  ) | author | runtests )
 var icon_required = 'uk-icon-check'
 var icon_optional = icon_required
 var icon_bonus  = icon_required
 var icon_unpublished = icon_required
 var iconoff = 'uk-icon-close'
 var iconview  =  ! ( this.props.displaystyle == 'detail' )
 if ( !  exercisefilter.required_exercises ){
    icon_required = iconoff
    }
 if ( ! exercisefilter.optional_exercises ){
    icon_optional = iconoff
    }
 if ( ! exercisefilter.bonus_exercises  ){
    icon_bonus= iconoff
  }
 var show_unpublished = true
 if ( ! exercisefilter.unpublished_exercises){
    var icon_unpublished = 'uk-icon-toggle-off'
    var show_unpublished = false
    var iconedit = 'uk-icon-circle-o'
    } else {
    var icon_unpublished = 'uk-icon-toggle-on'
    var iconedit = 'uk-icon-circle'
    }


 return(
 <span className="" >

        {  show_edit_toggle && iconview && author && (
            <button  onClick={() => this.handleToggle(exercisefilter,'unpublished_exercises',this.props.activeCourse)} data-uk-tooltip="delay:1500 ;   pos: right " 
            className="uk-button uk-button-small uk-width-1-4 uk-button-default unpublished_exercises"  >  
<i className={iconedit} /> Edit
    </button>  
        ) }
    
        {  show_obligatory && (
            <button  onClick={() => this.handleToggle(exercisefilter,'required_exercises',this.props.activeCourse)} data-uk-tooltip="delay:1500 ;   pos: right " title={mess0} 
            className="uk-button uk-button-small uk-text uk-text-small uk-width-1-4  blue required_exercises ">  <i className={icon_required} /> {sum01}:{sum02}:{sum03}:{sum04} </button>  
        ) }
        { show_bonus && (
            <button  onClick={() => this.handleToggle(exercisefilter,'bonus_exercises',this.props.activeCourse)} 
            data-uk-tooltip="delay:1500; pos: right" title={mess1}
            className="uk-button uk-width-1-4 uk-button-small   gold bonus_exercises ">  <i className={icon_bonus} />
        {sum11}:{sum12}:{sum13}:{sum14} </button>   
        )}
        { show_optional && (
            <button  onClick={() => this.handleToggle(exercisefilter,'optional_exercises',this.props.activeCourse)} 
            data-uk-tooltip="delay:1500; pos: right" title={mess2} 
            className="uk-button uk-width-1-4 uk-button-small  green optional_exercises ">  <i className={icon_optional} />{sum21}:{sum22}:{sum23}:{sum24} </button>  
        )}
        <button className="uk-button uk-hidden-small">{username}</button> 
    </span>
    )
  }

}


const mapStateToProps = state => {
  var activeCourse = state.getIn(['activeCourse'])
   return ( {
    exerciseState: state.get("exerciseState"),
    displaystyle: state.get("displaystyle"),
    student: state.getIn(["login", "groups"], immutable.List([])).includes("Student"),
    author: state.getIn(["login", "groups"], immutable.List([])).includes("Author"),
    course: state.getIn(['courses', activeCourse, 'course_name'], ""),
    username: state.getIn(['exerciseState','username'],''),
    iframed: state.getIn(['iframed'] , false),
    exercisefilter : state.getIn(['exercisefilter']),
    activeCourse :   state.get('activeCourse'),

    }
    )
 }

const mapDispatchToProps = dispatch => {
  return {
    onHome: () => dispatch(navigateMenuArray([])),
    onExerciseFilterChange: (exercisefilter, activeCourse) => {
            dispatch(updateExerciseFilter(exercisefilter))
            dispatch(fetchExerciseTree(activeCourse) )
        }

  }
}

export default connect( mapStateToProps, mapDispatchToProps)(BaseSummaryBar);
