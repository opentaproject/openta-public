import { insertImplicitSubscript } from '../mathrender/string_parse.js'
import { enforceList } from '../../immutablehelpers.js';
import immutable, { List } from 'immutable';

"use strict"; // It is recommended to use strict javascript for easier debugging

function uniquecat(a,b) {
	var c = a.concat(b.filter(function (item) {
    		return a.indexOf(item) < 0;
	})) 
    return c
     };
 function parseVariableString( variableString ) {
    var vars = variableString.trim()
      .split(';')
      .filter(str => str !== "")
      .map( str => str.split('=') )
      .map( entry => insertImplicitSubscript(entry[0].trim()) );
      return vars;
  }

 function parseVariables(question) {
    // var varsList = parseVariableString(question.getIn(['global','$'], ''));
    var varsListGlobal1 = parseVariableString(question.getIn(['global','$'], ''));
//console.log("MATHEX varsListGlobal1=", varsListGlobal1 )
    var varsListGlobal2 =   enforceList( question.getIn(['global','var'], List([]))  ).map(
	item =>  ( item.getIn(['token','$']).trim() ) ).toJS()
//console.log("MATHEX varsListGlobal2=", varsListGlobal2 )
    var varsListLocal1 = parseVariableString(question.getIn(['variables','$'], ''));
//console.log("MATHEX varsListLocal1=", varsListLocal1)
    var varsListLocal2 = enforceList( question.getIn(['var','token','$'], List([]))).map(
	item => item.trim() ).toJS();
//console.log("MATHEX varsListLocal2=", varsListLocal2)
    var  varsUsed = question.get('usedvariablelist',List([])).toJS() ;
    if( varsUsed.length == 0 ){
	// console.log("Length is zero ");
	var correct_answer =  question.getIn(['expression','$'], '').replace(/;/g,'').trim();
 	var caretless = correct_answer;
	// console.log("correct_answer = ", correct_answer )
    	caretless = caretless.replace(/[A-Z,a-z,0-9]+\(/g,'(' )
 	// console.log("caretless = ", caretless )
	var rx = new RegExp("([A-Z,a-z]+\w*)","g")
	var lis = [];
	var match ;
	while((match = rx.exec(caretless)) !== null){
    		lis.push(match[0] );
		}
	// console.log("lis = ", lis )
	varsUsed = lis;
   	}	
    var baseunitsjs =  { coulomb:{"tex":"C"},
 			joule:{"tex":"J"},
			meter:{"tex":"m"},
   			kg:{"tex":"kg"},
			volt:{"tex":"V"},
 			kelvin:{"tex":"K"},
			meter:{"tex":"m"},
			second:{"tex":"s"},
			}
    var baseunits = immutable.fromJS( baseunitsjs);
////console.log("MATHEX: baseunits = ", JSON.stringify( baseunits ,'null','\t') )
////console.log("MATHEX varsUsed =", varsUsed)
    var globalvarPropsList = enforceList(question.getIn(['global', 'var'], List([])));
    var localvarPropsList = enforceList(question.get('var', List([])));
    var allvarPropsList = localvarPropsList.concat(globalvarPropsList);
    var usethese = uniquecat( uniquecat( varsUsed, varsListLocal1 ), varsListLocal2 )
    var allpossibleVars = uniquecat(  usethese, uniquecat( varsListGlobal1, varsListGlobal2) )
//console.log("MATHEXPR: allpossibleVars", allpossibleVars)
    // console.log("usethese = ", usethese )
    //for(let v of allpossibleVars) {
    //  if(v.hasIn('token','$')) {
    //    var parsedVar = insertImplicitSubscript(v.getIn(['token','$'],'').trim()); 
    //    if( varsList.indexOf(parsedVar) == -1) {
    //      varsList.push(parsedVar);
    //    }
    //  }
   // }
    var varsList = uniquecat( usethese, Object.keys( baseunitsjs) )
    // console.log("varsList = ", varsList );
    // console.log("allvarPropsList= ", JSON.stringify( allvarPropsList ));
    var varProps = allvarPropsList.map( item => ({
      //The token is the key, the other items that are not the token or the special $children$ are added as a map.
      [item.getIn(['token', '$'], '').trim()]: item.filterNot( (val, key) => key === 'token' || key === '$children$' || key === '$').map( val => val.get('$') )
    }) )
    .reduce( (prev, next) => prev.merge(next), immutable.Map({}));
    //varProps = immutable.fromJS({"f":{},"c":{"tex":" C "},"h":{}} )
////console.log("MATHEX: varProps = ",  varProps  )
    // var addprops = immutable.fromJS({"f":{},"q":{"tex":" Q "},"h":{}} )
////console.log("MATHEX: baseunits = ",  JSON.stringify( baseunits ) )
   // varProps = varProps.concat( baseunits )
   varProps = baseunits.concat( varProps );
//console.log("MATHEX varProps", JSON.stringify( varProps ) );
   /* this.varsList = varsList;
   this.varProps = varProps;
   */
//console.log("MATHEX varsList = ", varsList )
//console.log("MATHEX varsUsed = ", varsUsed )
//console.log("MATHEX varsProps = ", varProps)
   return {'varsList': varsList,'varProps': varProps,'varsUsed':varsUsed,'allVars':allpossibleVars}
  }


export {uniquecat, parseVariableString, parseVariables }
