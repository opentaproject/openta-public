import immutable, { List } from 'immutable';
import { enforceList } from '../../immutablehelpers.js';
import { create, all } from 'mathjs';
const math = create(all);
import { insertImplicitSubscript } from '../mathrender/string_parse.js';

export const external_parseVariableString = (variableString, thiss) => {
  //console.log("variableString = ", variableString)
  var vars = variableString
    .trim()
    .split(';')
    .filter((str) => str !== '')
    .map((str) => str.split('='))
    .map((entry) => entry[0].trim());
  return vars;
};

export const external_parseVariables = (thiss) => {
  //console.log("PARSE VARIABLES")
  //console.log("PROPS", thiss.props.questionData.getIn(['global','$'], ''))
  if (thiss.props.questionData.getIn(['global', '$'], false)) {
    thiss.varsList = thiss.parseVariableString(thiss.props.questionData.getIn(['global', '$']));
  } else {
    thiss.varsList = [];
  }
  //console.log("THIS.VARSLITSTRING", thiss.varsList)
  var varPropsList = enforceList(thiss.props.questionData.getIn(['global', 'var'], List([])));
  var funcPropsList = enforceList(thiss.props.questionData.getIn(['global', 'func'], List([])));
  varPropsList = varPropsList.concat(funcPropsList);
  var localVars2 = enforceList(thiss.props.questionData.getIn(['variables', 'var'], List([])));
  var localVars1 = enforceList(thiss.props.questionData.getIn(['var'], List([])));
  var localVars = localVars2.concat(localVars1);
  var allVars = localVars.concat(varPropsList).concat(funcPropsList);
  for (let v of allVars) {
    if (v.hasIn('token', '$')) {
      var parsedVar = insertImplicitSubscript(v.getIn(['token', '$'], '').trim());
      if (thiss.varsList.indexOf(parsedVar) == -1) {
        thiss.varsList.push(parsedVar);
      }
    }
  }
  thiss.varProps = allVars
    .map((item) => ({
      [item.getIn(['token', '$'], '').trim()]: item
        .filterNot((val, key) => key === 'token' || key === '$children$' || key === '$')
        .map((val) => val.get('$'))
    }))
    .reduce((prev, next) => prev.merge(next), immutable.Map({}));
};

// newrenderAsciiMath = throttle( (asciitext,ignore_undefined=false ) => thiss.oldrenderAsciiMath( asciitext,ignore_undefined), 500 )
//renderAsciiMath =  (asciitext,ignore_undefined=false ) => thiss.oldrenderAsciiMath( asciitext,ignore_undefined)

export const external_parseBlacklist = (thiss) => {
  var blacklist = immutable.List([]);
  var globalBlacklistObject = thiss.props.questionData.getIn(['global', 'blacklist', 'token']);
  var blacklistObject = thiss.props.questionData.getIn(['blacklist', 'token']);
  if (globalBlacklistObject) {
    blacklist = blacklist.concat(enforceList(globalBlacklistObject));
  }
  if (blacklistObject) {
    blacklist = blacklist.concat(enforceList(blacklistObject));
  }
  thiss.blacklist = blacklist.map((item) => insertImplicitSubscript(item.get('$', '').trim())).toJS();
};
