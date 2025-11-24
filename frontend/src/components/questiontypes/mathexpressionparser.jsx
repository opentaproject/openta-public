// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react'; // React specific import
import { enforceList } from '../../immutablehelpers.js';
import immutable, { List } from 'immutable';
import { units } from './units.js';
import MathSpan from '../MathSpan.jsx';
import T from '../Translation.jsx';

('use strict'); // It is recommended to use strict javascript for easier debugging

function uniquecat(a, b) {
  if (a === undefined) {
    return b;
  } else if (b === undefined) {
    return a;
  }
  var c = a.concat(
    b.filter(function (item) {
      return a.indexOf(item) < 0;
    })
  );
  return c;
}
function anotinb(a, b) {
  var c = a.filter((x) => !~b.indexOf(x));
  return c;
}
function parseVariableString(variableString) {
  var vars = variableString
    .trim()
    .split(';')
    .filter((str) => str !== '')
    .map((str) => str.split('='));
  // .map( entry => insertImplicitSubscript(entry[0].trim()) );
  return vars;
}

function parseVariables(question) {
  // var varsList = parseVariableString(question.getIn(['global','$'], ''));
  // console.log("MATHEXPRESSIONPARSER question = ", JSON.stringify( question) )
  var varsListGlobal1 = parseVariableString(question.getIn(['global', '$'], ''));
  //console.log("MATHEX varsListGlobal1=", varsListGlobal1 )
  var varsListGlobal2 = enforceList(question.getIn(['global', 'var'], List([])))
    .map((item) => item.getIn(['token', '$']).trim())
    .toJS();
  //console.log("MATHEX varsListGlobal2=", varsListGlobal2 )
  var varsListLocal1 = parseVariableString(question.getIn(['variables', '$'], ''));
  //console.log("MATHEX varsListLocal1=", varsListLocal1)
  var varsListLocal2 = enforceList(question.getIn(['var', 'token', '$'], List([])))
    .map((item) => item.trim())
    .toJS();
  //console.log("MATHEX varsListLocal2=", varsListLocal2)
  var varsUsed = question.get('usedvariablelist', List([])).toJS();
  if (false && varsUsed.length == 0) {
    // console.log("Length is zero ");
    var correct_answer = question.getIn(['expression', '$'], '').replace(/;/g, '').trim();
    var caretless = correct_answer;
    // console.log("correct_answer = ", correct_answer )
    caretless = caretless.replace(/\^/g, ' ');
    caretless = caretless.replace(/[A-z][A-Za-z0-9]*\(/g, '(');
    //console.log("caretless = ", caretless )
    var rx = new RegExp('([A-z][A-z0-9]*)', 'g');
    var lis = [];
    var match;
    while ((match = rx.exec(caretless)) !== null) {
      lis.push(match[0]);
    }
    // console.log("lis = ", lis )
    varsUsed = lis;
  }
  //var baseunitsjs =  { coulomb:{"tex":"C"},
  //			joule:{"tex":"J"},
  //			meter:{"tex":"m"},
  //  			kg:{"tex":"kg"},
  //			volt:{"tex":"V"},
  //			kelvin:{"tex":"K"},
  //			meter:{"tex":"m"},
  //			second:{"tex":"s"},
  //			I:{"tex":"i"}
  //			}
  var baseunits = immutable.fromJS(units);
  ////console.log("MATHEX: baseunits = ", JSON.stringify( baseunits ,'null','\t') )
  //   console.log("MATHEX varsUsed 2 =", varsUsed)
  var globalvarPropsList = enforceList(question.getIn(['global', 'var'], List([])));
  var localvarPropsList = enforceList(question.get('var', List([])));
  var localvarPropsList2 = enforceList(question.getIn(['variables', 'var'], List([])));
  //console.log("localvarPropsList2 = ", JSON.stringify( localvarPropsList2  ) )
  var allvarPropsList = localvarPropsList.concat(globalvarPropsList);
  var usethese = uniquecat(uniquecat(varsUsed, varsListLocal1), varsListLocal2);
  var allpossibleVars = uniquecat(usethese, uniquecat(varsListGlobal1, varsListGlobal2));
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
  // var varsList = uniquecat( usethese, Object.keys( baseunitsjs) )
  var varsList = usethese;
  // console.log("varsList = ", varsList );
  // console.log("allvarPropsList= ", JSON.stringify( allvarPropsList ));
  var varProps = allvarPropsList
    .map((item) => ({
      //The token is the key, the other items that are not the token or the special $children$ are added as a map.
      [item.getIn(['token', '$'], '').trim()]: item
        .filterNot((val, key) => key === 'token' || key === '$children$' || key === '$')
        .map((val) => val.get('$'))
    }))
    .reduce((prev, next) => prev.merge(next), immutable.Map({}));
  //varProps = immutable.fromJS({"f":{},"c":{"tex":" C "},"h":{}} )
  ////console.log("MATHEX: varProps = ",  varProps  )
  // var addprops = immutable.fromJS({"f":{},"q":{"tex":" Q "},"h":{}} )
  ////console.log("MATHEX: baseunits = ",  JSON.stringify( baseunits ) )
  // varProps = varProps.concat( baseunits )
  varProps = baseunits.concat(varProps);
  //console.log("MATHEX varProps", JSON.stringify( varProps ) );
  /* this.varsList = varsList;
   this.varProps = varProps;
   */
  //console.log("MATHEX varsList = ", varsList )
  //console.log("MATHEX varsUsed = ", varsUsed )
  //console.log("MATHEX varsProps = ", varProps)
  return { varsList: varsList, varProps: varProps, varsUsed: varsUsed, allVars: allpossibleVars };
}

function parseBlacklist(question) {
  var blacklist = immutable.List([]);
  var globalBlacklistObject = question.getIn(['global', 'blacklist', 'token']);
  var blacklistObject = question.getIn(['blacklist', 'token']);
  if (globalBlacklistObject) {
    blacklist = blacklist.concat(enforceList(globalBlacklistObject));
  }
  if (blacklistObject) {
    blacklist = blacklist.concat(enforceList(blacklistObject));
  }
  blacklist = blacklist.map((item) => item.get('$', '').trim()).toJS();
  return blacklist;
}

function usethesevariables(question) {
  var exposeglobals = question.get('exposeglobals');
  var blacklist = parseBlacklist(question);
  var res = parseVariables(question);
  var varsList = res['varsList'];
  var varProps = res['varProps'];
  var varsUsed = res['varsUsed'];
  var allVars = res['allVars'];
  // var  n_attempts =  state.getIn(['n_attempts'],'23');
  // console.log("n_attempts = ", n_attempts);
  var localVars = parseVariableString(question.getIn(['variables', '$'], ''));
  //console.log("MATHEXPRESSION localVars = ", localVars )
  //console.log("MATHEXPRESSION exposeglobals = ", exposeglobals )
  //console.log("MATHEXPRESSION varsList : ", varsList);
  var mathjsEvalVars = {};
  var availableVariables = [];
  // console.log("MATHEXPRESSION EXPOSEGLOBALS = ", exposeglobals)
  if (exposeglobals) {
    //console.log("mathexpression QUESTION_DEV EXPOSEGLOBALS TRUE");
    var usethesevars = allVars; // THIS WAS THE ORIGINAL; ALL VARIABLE NAMES ARE EXPOSED UNLESS BLACKLISTED
  } else {
    //console.log("mathexpression QUESTION_DEV EXPOSEGLOBALS FALSE");
    usethesevars = varsList;
  }
  usethesevars = anotinb(usethesevars, ['I', 'e', 'pi']);
  // console.log("MATEXPRESSIONE usethesevars", usethesevars )
  return usethesevars;
}

function AvailableVariables(question) {
  // var  exposeglobals =  question.get('exposeglobals');
  var blacklist = parseBlacklist(question);
  var res = parseVariables(question);
  // var varsList = res['varsList'];
  var varProps = res['varProps'];
  //console.log("VARPROPS = ", varProps )
  // var varsUsed = res['varsUsed'];
  // var allVars = res['allVars'];
  // var  n_attempts =  state.getIn(['n_attempts'],'23');
  // console.log("n_attempts = ", n_attempts);
  // var localVars = parseVariableString(question.getIn(['variables','$'], ''));
  // console.log("MATHEXPRESSION localVars = ", localVars )
  // console.log("MATHEXPRESSION exposeglobals = ", exposeglobals )
  // console.log("MATHEXPRESSION this.varsList : ", varsList);
  var mathjsEvalVars = {};
  var availableVariables = [];
  // console.log("MATHEXPRESSION EXPOSEGLOBALS = ", exposeglobals)
  /*
 if( exposeglobals ){
	//console.log("mathexpression QUESTION_DEV EXPOSEGLOBALS TRUE");
  	var usethesevars = allVars; // THIS WAS THE ORIGINAL; ALL VARIABLE NAMES ARE EXPOSED UNLESS BLACKLISTED
 	} else {
	//console.log("mathexpression QUESTION_DEV EXPOSEGLOBALS FALSE");
 	usethesevars = varsUsed;
 	}
  */
  var usethesevars = usethesevariables(question);
  // console.log("MATEXPRESSIONE usethesevars", usethesevars )
  if (usethesevars.length > 0) {
    usethesevars.map((v) => {
      mathjsEvalVars[v] = 1;
    });
    // availableVariables.push( (<span key="s">(i termer av </span>) );
    availableVariables.push(
      <span key="s">
        {' '}
        <T>in terms of</T>{' '}
      </span>
    );

    var filteredVars = usethesevars
      .filter((v) => typeof v === 'string' && blacklist.indexOf(v) == -1)
      .map((v) => v.replace(/\_/g, ''));
    for (const [i, v] of filteredVars.entries()) {
      availableVariables.push(<span key={'v' + i}>{v}</span>);
      if (varProps.hasIn([v, 'tex'])) {
        availableVariables.push(
          <span key={'tex' + i}>
            {' '}
            (<MathSpan message={'$' + varProps.getIn([v, 'tex']) + '$'}></MathSpan>)
          </span>
        );
      }
      if (i < filteredVars.length - 1) {
        availableVariables.push(<span key={'c' + i}>, </span>);
      }
    }
    availableVariables.push(<span key={'e'}></span>);
  }
  // console.log("MATHEXPRESSIONPARSER ", availableVariables)
  return availableVariables;
}

export { usethesevariables, uniquecat, parseBlacklist, parseVariableString, parseVariables, AvailableVariables };
