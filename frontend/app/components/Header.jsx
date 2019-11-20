import React from "react";
import { connect } from "react-redux";
import { navigateMenuArray } from "../menu.js";
import T from "./Translation.jsx";
import t from "../translations.js";
import LoginInfo from "./LoginInfo.jsx"
import SummaryBar from "./SummaryBar.jsx"
import UpdateDisplayStyle from "./UpdateDisplayStyle"

import immutable from "immutable";
import moment from "moment";
import { SUBPATH } from "../settings.js";


const BaseHeader = ({
     student,
     exerciseState,
     onHome,
      author,
  displaystyle,
  iframed,
  course,
  show_home,
  exercisefilter,
  show_edit_toggle,
}) => {
  var summary = exerciseState.getIn(['summary'],'SUMMARY MISSING')
  var sums =  exerciseState.getIn(['sums'], immutable.List( []) )
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

  
  var mess2 =    ( "Obligatory: " + sum21  + " correct and ontime " ) 
  mess2 = mess2 + ( ( 0 !== sum22  )   ? ( ", " + sum22 + "correct but late " ) : ''    )
  mess2 = mess2 + ( ( 0 !== sum23  )   ? ( ", " + sum23 + " unchecked ontime " ) : ''   )
  mess2 = mess2 + (  ( 0 !== sum24  )   ? ( ", " + sum24 + " unchecked late " ) : ''   )
 
 var level = 0
 var use_header = true
 var runtests = exerciseState.getIn(['runtests'] ,false)
 var force_all_header_buttons = true

  
 var show_logininfo_button = true == (  author | runtests )
 var show_logininfo = true == ( author | runtests )
 return(
        <div className="border-top uk-width-1-1" >
        <div>
        <div className="uk-button-group uk-width-1-3">
        <a className="uk-button uk-hidden" href="#"> </a>
        { show_logininfo_button && ( <button className="uk-width-1-3 uk-button " data-uk-toggle="{target:'.login-info'}"><i className="uk-icon-chevron-circle-up uk-hidden login-info"/>
        <i className="uk-icon-chevron-circle-down uk-visible login-info"/></button> 
        )}
        { !show_logininfo_button && ( <div className="uk-width-1-3"> </div>)}
        { ( show_home ) && (  <button className="uk-button onHome" onClick={onHome}> 
          {/* THE <a> TAG NEXT IS JUST FOR RUNTESTS */}
          <a href="#" className='onHome'> <i className="uk-icon  uk-icon-home"></i>  </a> </button>    
          )}
        { ( ! show_home ) && ( <UpdateDisplayStyle />) }
        </div>

      { ! show_home && (
        <div className="uk-button-group  uk-width-1-3">
        <a className="uk-button uk-hidden" href="#"> </a>
        <SummaryBar show_edit_toggle={show_edit_toggle}  />
        </div>
      )}


        
        <div className="uk-width-1-6  uk-padding-remove  uk-align-right">

            {  !iframed && ( <div className='uk-padding-remove  uk-width-1-1'>  <a title="Logga ut" href={SUBPATH + "/logout/" + course + '/'}>
                    <span className="uk-width-1-1 uk-visible-large"> {course} </span><i className="uk-icon uk-icon-sign-out uk-text-small uk-text-middle"></i></a> 
                     </div>)} 
            {iframed && ( <div className='uk-padding-remove  uk-width-1-1'> <a title="Logga ut" href={SUBPATH + "/logout/" + course + '/lti_login/'}><span className="uk-width-1-1 uk-visible-large"> 
                {course} </span><i className="uk-icon uk-icon-rotate-right uk-text-large uk-text-middle"></i></a> </div>) 
                } 
        </div> 

        <div className="pix30">

        {   show_logininfo &&       ( <div className=" uk-padding-remove uk-width-1-1  login-info"><LoginInfo /></div>   ) }
        {   ! show_logininfo_button &&    ( <div className=" uk-margin-remove uk-padding-remove uk-width-1-1 uk-hidden login-info"><LoginInfo /></div>   )  }

        </div>

        </div>
        </div>
    )
}



const mapStateToProps = state => {
  var activeCourse = state.getIn(['activeCourse'])
   return ( {
    exerciseState: state.get("exerciseState"),
    displaystyle: state.get("displaystyle"),
    student: state.getIn(["login", "groups"], immutable.List([])).includes("Student"),
    author: state.getIn(["login", "groups"], immutable.List([])).includes("Author"),
    course: state.getIn(['courses', activeCourse, 'course_name'], ""),
    iframed: state.getIn(['iframed'] , false),
    exercisefilter: state.get('exercisefilter'),
    }
    )
 }

const mapDispatchToProps = dispatch => {
  return {
    onHome: () => dispatch(navigateMenuArray([])),
  }
}

export default connect( mapStateToProps, mapDispatchToProps)(BaseHeader);
