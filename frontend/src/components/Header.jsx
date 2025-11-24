import React from 'react';
import { connect } from 'react-redux';
import { navigateMenuArray } from '../menu.js';
import T from './Translation.jsx';
import t from '../translations.js';
import LoginInfo from './LoginInfo.jsx';
import SummaryBar from './SummaryBar.jsx';
import UpdateDisplayStyle from './UpdateDisplayStyle';
import BugReport from './BugReport'

import immutable from 'immutable';
import { SUBPATH, use_sidecar ,sidecar_url } from '../settings.js';

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
  course_name,
  anonymous,
  username,
  activeExercise,
  pk,
  sidecar_count,
}) => {
  try { 
  	sidecar_count = sidecar_count.get('sidecar_count',23)
  } catch {
	 sidecar_count = -1
  }
  var summary = exerciseState.getIn(['summary'], 'SUMMARY MISSING');
  var sums = exerciseState.getIn(['sums'], immutable.List([]));
  var show_optional = sums.getIn(['optional', 'feedback', 'n_correct'], 0);
  var show_bonus = sums.getIn(['bonus', 'feedback', 'n_correct'], 0);
  var show_obligatory = sums.getIn(['obligatory', 'feedback', 'n_correct'], 0);
  var level = 0;
  var use_header = true;
  var runtests = exerciseState.getIn(['runtests'], false);
  var force_all_header_buttons = true;

  var hide_logininfo = !(author || runtests);
  //var hide_logininfo_button = true
  //var hide_logininfo = true
  var authenticated = !anonymous;
  var msgpopup =
    'You are using this site anonymously. If you log out, you will lose your work and have to start over. You should register if you want to continue working. Registration is free, but you will need valid email.';
  //var msgpopup = t("You are using this site anonymously.  If you log out, you will lose your work and have to start over. ")
  if (!authenticated) {
    return (
      <div className="uk-text uk-margin-small-left uk-align-middle">
        <button className="uk-button uk-button-link Home onHome" onClick={onHome}>
          {' '}
          <i className="uk-icon  uk-icon-small uk-icon-home"></i>{' '}
        </button>

        <a href={'/register_by_domain/' + pk + '/' + username}>
          <span className="uk-button uk-text-baseline uk-button-link uk-text-size">
            {' '}
            <T>Register</T>{' '}
          </span>{' '}
        </a>

        <span className="uk-hidden-small uk-text-size"> {course_name} </span>
        {/* <a title="Logga ut" href={SUBPATH + "/logout/" + course_name + '/'}>
                          <span className="uk-text-size"> Logout </span>
                            </a>  */}

        <a
          onClick={(e) =>
            UIkit.modal.confirm(t(msgpopup), () => window.open(SUBPATH + '/logout/' + course_name + '/', '_self'), {
              labels: {
                Ok: t('Logout and delete my answers.'),
                Cancel: t('Cancel logout and keep working anonymously!')
              }
            })
          }
          className="uk-margin-small-left uk-text-size"
          data-uk-tooltip
          title="LOGOUT "
        >
          {' '}
          <T>Logout</T>{' '}
        </a>
      </div>
    );
  }
  var show_listview = show_obligatory || show_bonus;
  show_home = true;
  show_listview = true;
  var sidecar_text = String( sidecar_count)
  sidecar_text = ''
  if ( sidecar_count  <  0  ){
	  sidecar_text = ''
	  var sidecar_icon = ''
  	} else if ( sidecar_count  ==  0  ){
	  var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/s.ico" 
  	} else  { 
	  var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/ss.png" 
  	}
  return (
    <div className="border-top ">
      <div>
        <div className="uk-button-group uk-width-1-3">
          <a className="uk-button uk-hidden" href="#">
            {' '}
          </a>
          <button className="uk-button " data-uk-toggle="{target:'.login-info'}">
            <i className="uk-icon-chevron-circle-up uk-hidden login-info" />
            <i className="uk-icon-chevron-circle-down uk-visible login-info OpenHeader" />
          </button>G
          {(runtests || show_home) && (
            <div>
              <button className="uk-button Home onHome" onClick={onHome}>
                {' '}
                <i className="uk-icon  uk-icon-home"></i>{' '}
              </button>
              {use_sidecar != 'False' && sidecar_count >= 0 && (
                <span>
                  <a className="uk-vertical-align button-link" href={"/launch_sidecar?filter_key="}>
                    <img style={{ marginTop: '4px', width: '32px', height: 'auto' }} src={sidecar_icon} />
                  </a>
                  <button className="uk-buton uk-button-link"> {sidecar_text} </button>
                </span>
              )}
            </div>
          )}
          {show_listview && !anonymous && (
            <span className="">
              {' '}
              <UpdateDisplayStyle />{' '}
            </span>
          )}
	  <BugReport username={username} subdomain={course} admin={author} />
        </div>

        {authenticated && (
          <div className="uk-button-group">
            <a className="uk-button uk-hidden" href="#">
              {' '}
            </a>
            <SummaryBar exercisefilter={exercisefilter} show_edit_toggle={show_edit_toggle} />
          </div>
        )}

        {true && (
          <div className="uk-hidden-small uk-align-right">
            {authenticated && !iframed && (
              <div className="uk-padding-large">
                {!anonymous && (
                  <a title="Change password" href={SUBPATH + '/change_password/?next='}>
                    <i className="uk-padding-large uk-icon uk-icon-key uk-text-medium"></i>
                  </a>
                )}
                <a title="Logga ut" href={SUBPATH + '/logout/' + course_name + '/'}>
                  <span className=""> {course_name} </span>
                  <i className="uk-icon uk-icon-sign-out  uk-text-middle"></i>
                </a>
              </div>
            )}
            {authenticated && iframed && (
              <div className="  ">
                <a title="Change password" href={SUBPATH + '/change_password/?next='}>
                  <i className="uk-icon uk-icon-key uk-text-medium"></i>
                </a>
                <a title="Logga ut" href={SUBPATH + '/logout/' + course_name + '/lti_login/'}>
                  <span className="">{course} </span>
                  <i className="uk-icon uk-icon-rotate-right uk-text-size uk-text-middle"></i>
                </a>{' '}
              </div>
            )}
          </div>
        )}

        <div className="pix30">
          {hide_logininfo && (
            <div className="    uk-hidden login-info">
              <LoginInfo />
            </div>
          )}
          {!hide_logininfo && (
            <div className="    uk-visible login-info">
              <LoginInfo />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const mapStateToProps = (state) => {
  var activeCourse = state.getIn(['activeCourse']);
  return {
    exerciseState: state.get('exerciseState'),
    displaystyle: state.get('displaystyle'),
    student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    anonymous: state.getIn(['login', 'groups'], immutable.List([])).includes('AnonymousStudent'),
    course: state.getIn(['courses', activeCourse, 'course_name'], ''),
    iframed: state.getIn(['iframed'], false),
    exercisefilter: state.get('exercisefilter'),
    course_name: state.getIn(['course', 'course_name']),
    pk: state.getIn(['course', 'pk']),
    username: state.getIn(['login', 'username']),
    sidecar_count:  state.getIn(['login','sidecar_count'],  immutable.List([])  ),
    activeExercise: state.getIn(['activeExercise'],null)
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onHome: () => dispatch(navigateMenuArray([]))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseHeader);
