import React from "react";
import { connect } from "react-redux";
import { navigateMenuArray } from "../menu.js";
import UpdateDisplayStyle from "./UpdateDisplayStyle.jsx";
import T from "./Translation.jsx";
import t from "../translations.js";

import immutable from "immutable";
import moment from "moment";
import { SUBPATH } from "../settings.js";


const BaseFooter = ({
     student,
     exerciseState,
     onHome,
      author,
  displaystyle,
}) => {
  var summary = exerciseState.getIn(['summary'],'SUMMARY MISSING')
  var sums =  exerciseState.getIn(['sums'], immutable.List( []) )
  var sum01 = sums.getIn(['required','feedback','number_complete_by_deadline'],0)
  var sum02 = sums.getIn(['required','feedback','number_complete'],0) - sum01
  var sum03 = sums.getIn(['required','nofeedback','number_complete_by_deadline'],0)
  var sum04 = sums.getIn(['required','nofeedback','number_complete'],0) - sum03

  var sum11 = sums.getIn(['bonus','feedback','number_complete'],0)
  var sum12 = sum11 - sums.getIn(['bonus','feedback','number_complete_by_deadline'],0)
  var sum13 = sums.getIn(['bonus','nofeedback','number_complete'],0)
  var sum14 = sum13 - sums.getIn(['bonus','nofeedback','number_complete_by_deadline'],0)

  
  var sum21 = sums.getIn(['optional','feedback','number_complete'],0)
  var sum22 = sum21 - sums.getIn(['optional','feedback','number_complete_by_deadline'],0)
  var sum23 = sums.getIn(['optional','nofeedback','number_complete'],0)
  var sum24 = sum23 - sums.getIn(['optional','nofeedback','number_complete_by_deadline'],0)

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

  

 return( 

        <div className="footer uk-align-center uk-margin-remove uk-padding-remove uk-grid uk-width-1-1 uk-child-width-1-6 uk-align-center">
        <div className="uk-padding-remove uk-width-1-6" > <button className="uk-button  uk-width-1-1 brand onHome" onClick={onHome}> <i className="uk-icon  uk-icon-home"></i> </button>   </div>
        <div className='uk-padding-remove uk-width-1-6'> <UpdateDisplayStyle />  </div> 
        <div className='uk-padding-remove uk-width-1-6'> <button className="uk-button uk-width-1-1 uk-visible-toggle-@s" data-uk-toggle="{target:'.login-info'}"><i className="uk-icon-cog"/></button> </div> 
         <div className='uk-padding-remove uk-width-1-6'><button data-uk-tooltip="delay:1500 ;   pos: right " title={mess0} 
            className="uk-button uk-width-1-1  uk-button-primary">  {sum01}:{sum02}:{sum03}:{sum04} </button>  </div> 
        <div className='uk-padding-remove uk-width-1-6'> <button 
            data-uk-tooltip="delay:1500; pos: right" title={mess1}
            className="uk-button   uk-width-1-1 gold"> {sum11}:{sum12}:{sum13}:{sum14} </button>  </div> 
        <div className='uk-padding-remove uk-width-1-6'>  <button 
            data-uk-tooltip="delay:1500; pos: right" title={mess2} 
            className="uk-button uk-width-1-1  uk-button-success"> {sum21}:{sum22}:{sum23}:{sum24} </button>  </div> 
        </div>

 )

     
}
const mapStateToProps = state => ({
  exerciseState: state.get("exerciseState"),
  displaystyle: state.get("displaystyle"),
  student: state.getIn(["login", "groups"], immutable.List([])).includes("Student"),
  author: state.getIn(["login", "groups"], immutable.List([])).includes("Author"),
});

const mapDispatchToProps = dispatch => {
  return {
    onHome: () => dispatch(navigateMenuArray([])),
  }
}
export default connect( mapStateToProps, mapDispatchToProps)(BaseFooter);
