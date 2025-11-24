// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import { notifyMissingString } from '../fetchers/fetch_translations.js';
import { getkey } from '../getkey.js';

var unstableKey = 7237;
const nextUnstableKey = () => unstableKey++;

//function getkey(string ){
//    var altkey = string.replace(/\s+/g,'')
//    var ret =  md5(altkey).substring(0,5)
//    //console.log(string, ret )
//    return ret
//    }

class BaseTranslation extends Component {
  //   constructor() {
  //      super();
  //     }
  //componentDidMount() {
  //console.log("DID MOUNT")
  //console.log("MOUNT THIS.PROPS.TRANSLATIONS", this.props.translations.size )
  //    }
  // componentDidUpdate() {
  //var nkey =  md5( this.props.children.replace(/\s+/g,'') ).substring(0,5)
  //var stringout = this.props.dict( nkey, this.props.language)
  //this.stringout = stringout
  //console.log("DID UPDATE", this.props.children)
  //console.log("THIS.PROPS.TRANSLATIONS", this.props.translations.size )
  //console.log("STRINGOUT = ", stringout)
  //   }
  render() {
    if (!this.props.use_translations) {
      return this.props.children;
    }
    var translations = this.props.translations;
    var dicts = this.props.dicts;
    var dict = this.props.dict;
    var children = this.props.children;
    //var nkey =  getkey( this.props.children)  // md5( this.props.children.replace(/\s+/g,'') ).substring(0,5)
    var nkey = getkey(this.props.children); // md5( this.props.children.replace(/\s+/g,'') ).substring(0,5)
    var language = this.props.language;
    var stringout = dict(nkey, language);
    var course = this.props.course;
    var go1 = !this.props.pendingState.getIn(['loadingExercises']);
    var go2 = !this.props.pendingState.getIn(['loadingExerciseTree']);
    if (stringout == false && go1 && go2 && !(this.props.translations == {})) {
      if (!dicts(nkey) && this.props.admin) {
        //console.log("Translations: ", go1 , go2, language, nkey , this.props.children)
        this.props.onNotifyMissingString(children, nkey, course, language);
      }
      stringout = children;
    }

    return <span className="uk-margin-small-left uk-text-size"> {stringout} </span>;
  }
}

const mapDispatchToProps = (dispatch) => ({
  onNotifyMissingString: (children, nkey, course, language) => {
    dispatch(notifyMissingString(children, nkey, course, language));
  }
});

const mapStateToProps = (state) => {
  const defaultLanguage = state.getIn(['course', 'languages', 0], 'en');
  const activeCourse = state.get('activeCourse');
  return {
    course: state.get('activeCourse'),
    pendingState: state.getIn(['pendingState', 'course']),
    translations: state.getIn(['translations'], {}),
    use_translations: state.getIn(['courses', activeCourse, 'use_auto_translation']),
    language: state.getIn(['lang'], defaultLanguage),
    dict: (altkey, lang) => state.getIn(['translations', altkey, lang], false),
    dicts: (altkey) => state.getIn(['translations', altkey], false),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin')
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseTranslation);
