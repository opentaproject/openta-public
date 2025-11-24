import React, { Component } from 'react';

import { connect } from 'react-redux';
import {
  fetchExercise,
  fetchExerciseRemoteState,
  fetchUserExercises,
  fetchSameFolder,
  fetchAddExercise,
  fetchMoveExercise,
  fetchExerciseTree
} from '../fetchers.js';

import { updatePendingStateIn, resetSelectedExercises } from '../actions.js';

import { setDetailResultsView, updateExercises, updateExerciseTreeUI } from '../actions.js';

import { navigateMenuArray } from '../menu.js';
import ExerciseItem from './ExerciseItem.jsx';
import Spinner from './Spinner.jsx';
import AddExercise from './AddExercise.jsx';
import FolderButtonCapture from './FolderButtonCapture.jsx';
import T from './Translation.jsx';

import immutable from 'immutable';
import { new_folder } from '../settings.js';

var difficulties = {
  1: 'Easy',
  2: 'Medium',
  3: 'Hard',
  none: ''
};

/* exercisetree, exerciseTreeUI, exerciseState, pendingState, currentpath, onExerciseClick,
  showStatistics, statistics, activityRange, onFolderLeftClick, student, onExerciseAdd,
  pendingExerciseAdd, author, lti_login, displaystyle, user_pk */

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

class BaseCourse extends Component {
  constructor() {
    super();
    this.state = { button: '0' };
    this.handleChange = this.handleChange.bind(this);
  }

  handleChange = (e, child, exercises, coursePk) => {
    console.log("handleChange Course")
    this.setState({ button: this.state.button + 1 });
    if (1 == e.buttons || !this.props.exercisefilter.organize) {
      return this.props.onFolderLeftClick(e, child.path, child.folded);
    }
    if (2 == e.buttons) {
      console.log("RIGHT CLICK FOLDER")
      return this.props.onFolderRightClick(e, child.path, exercises, coursePk);
    }
  };

  UNSAFE_componentWillMount(props, state, root) {
    if (this.props.user_pk && this.props.activeCourse) {
      fetchUserExercises(this.props.activeCourse, this.props.user_pk);
    }
    this.compact = this.props.compact ? true : false;
    if (this.props.onExerciseClick) {
      this.onExerciseClick = this.props.onExerciseClick;
    } else {
      this.onExerciseClick = this.props.onDefaultExerciseClick;
    }
    this.onExerciseClick = this.props.onDefaultExerciseClick;
  }

  //componentDidMount(props, state, root) {
  // }

  flatten = (arr) => {
    return arr.reduce((flat, toFlat) => flat.concat(Array.isArray(toFlat) ? flatten(toFlat) : toFlat), []);
  };

  countFinished = (folder, name, type) => {
    if (folder.has('exercises')) {
      var results = folder
        .get('exercises')
        .filter((e) => e.getIn(['meta', type]))
        .map((e, key) => this.props.exerciseState.getIn([key, 'correct'], false));
      return {
        total: results.size,
        correct: results.filter((x) => x).size
      };
    } else {
      return {
        total: 0,
        correct: 0
      };
    }
  };

  parseFolder = (folder, foldername, level = 0, displaystyle) => {
    var exercises = immutable.List([]),
      children = [];

    var rowbegin = '';
    var rowend = '';
    if (displaystyle == 'detail') {
      var rowbegin = '<tr>';
      var rowend = '</tr>';
      domstyle = '';
    }
    if (folder.has('exercises')) {
      exercises = folder.get('order').map((exercise) => {
        var default_name = folder.getIn(['exercises', exercise, 'name']);
	//console.log("NAME = ", default_name )
	if ('invisible' == default_name.trim()  ){
		return ''
	} 
	var lang = this.props.lang;
        var translated_names = folder.getIn(['exercises', exercise, 'translated_name'], immutable.Map({}));
        var exercisename = 'A' + translated_names.getIn([lang], default_name) + 'A' ;
        var meta = folder.getIn(['exercises', exercise, 'meta']);
        var published = meta.get('published', false);
        if (published || !this.compact || this.props.exercisefilter['unpublished_exercises']) {
          return (
            <li id={exercise} className="course-exercise-item" key={exercise + 'course-exercise-item'}>
              <ExerciseItem
                exercise={exercise}
                exerciseState={this.props.exerciseState}
                metaImmutable={meta}
                folder={folder}
                compact={this.compact}
                foldername={foldername}
                onExerciseClick={this.onExerciseClick}
                showStatistics={this.props.showStatistics}
                statistics={this.props.statistics}
                activityRange={this.props.activityRange}
                displaystyle={displaystyle}
                organize={this.props.exercisefilter.organize}
                subdomain={this.props.subdomain}
                author={this.props.author}
                exercisename={exercisename}
              />
            </li>
          );
        }
      });
    }
    var add_exercise = this.props.displaystyle !== 'detail' && !this.compact;
    var show_unpublished = this.props.exercisefilter['unpublished_exercises'];
    add_exercise = add_exercise && show_unpublished;
    if (add_exercise) {
      exercises = exercises.push(<AddExercise key="addExercise" path={folder.get('path')} />);
    }
    var new_folder_name = new_folder.split(':').pop();
    if (folder.has('folders')) {
      children = folder
        .get('folders', immutable.Map({}))
        .keySeq()
        .sort()
        .map((childfolder) => ({
          name: childfolder,
          folder: folder.getIn(['folders', childfolder, 'content']),
          content: this.parseFolder(
            folder.getIn(['folders', childfolder, 'content']),
            childfolder,
            level + 1,
            this.props.displaystyle
          ),
          path: folder.getIn(['folders', childfolder, 'content', 'path']),
          folded:
            new_folder == childfolder
              ? false
              : this.props.exerciseTreeUI.getIn(
                  folder.getIn(['folders', childfolder, 'content', 'path']).push('$folded$'),
                  true
                ),
          pending: this.props.exerciseTreeUI.getIn(
            folder.getIn(['folders', childfolder, 'content', 'path']).push('$pending$'),
            false
          )
        }));
    }
    var levelClass = '';
    switch (level) {
      case 1:
        levelClass = 'uk-block-muted';
        break;
      case 0:
        levelClass = 'uk-block-muted';
        break;
    }
    var domstyle = 'uk-thumbnav';
    if (this.props.displaystyle == 'detail') {
      var domstyle = 'uk-list uk-list-bullet uk-padding-remove uk-margin-remove';
      var use_header = true;
      var foldertext = 'uk-text-medium uk-margin-remove uk-padding-remove  ';
    } else {
      var foldertext = 'uk-text-large uk-margin-right';
      var use_header = false;
    }

    var minidom = (
      <div>
        <table className="uk-width-1-1 exercise_item">
          <tbody>
            <tr>
              <td className="uk-margin-remove uk-padding-remove uk-text-primary uk-text-bold column_name_head">
                {' '}
                exercise name
              </td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_due"> date due</td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_plus"> complete and ontime </td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_plus"> autograded answers </td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_plus"> image answers </td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_check"> Audit</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
    var selected = this.props.selectedExercises.length > 0;
    var instruction = selected ? 'cancel seleced exercises' : '';
    var createnew =
      this.props.exercisetree
        .getIn(['folders'], immutable.List([]))
        .keySeq()
        .filter((item) => new_folder == item)
        .toList().size == 0;
    var spacedom = (
      <div>
        {/*selected  &&  (  <div><div> <a href="" onClick={(e)=>this.props.onReset() }> Click to clear selected exercises </a> </div><div>
                            right-click 
                            <i key={nextUnstableKey()} className={"uk-icon uk-icon-mail-forward uk-margin-small-left"} />
                            to move selected exercise to this folder 
                              </div> </div> )  */}
        <table className="uk-width-1-1 exercise_item">
          <tbody>
            <tr>
              {/* createnew  && selected && (
        <td className="uk-margin-remove uk-padding-remove uk-text-primary uk-text-bold column_name_head">  
          <i className="uk-icon uk-icon-folder uk-margin-small-left" /> 
          <i key={nextUnstableKey()} className={"uk-icon uk-icon-mail-forward uk-margin-small-left"}
          onClick={(e) => this.props.onFolderRightClick(e, [new_folder] , this.props.selectedExercises,this.props.activeCourse) } />  
         new_folder </td> ) */}
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_due"> </td>
              <td className="uk-text-primary uk-text-bold column_date_plus"> </td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_plus"> </td>
              <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_plus"> </td>
              <td className="uk-hidden-small column_check"> </td>
            </tr>
          </tbody>
        </table>
      </div>
    );

    var DOMSUMMARY = (
      <div>
        {level == 0 && use_header && minidom}
        {level == 0 && !use_header && spacedom}
      </div>
    );

    //console.log("COURSSE subdomain = ", this.props.subdomain)
    const preventDefault = (e) => {
      e.preventDefault();
    };
    var selected = this.props.selectedExercises.length > 0;
    var instruction = selected ? 'YES' : 'NO';
    var organize = this.props.exercisefilter.organize;
    var author = this.props.author;
    var leftmessage = 'Move or rename folder';
    var rightmessage = 'Move selected here ';
    var motd = this.props.motd ? 'Message: ' + this.props.motd : '';
    var DOM = (
      <div key={nextUnstableKey()} className="uk-margin-remove uk-padding-remove">
        <div className={'uk-block uk-padding-remove ' + levelClass}>
          {level == 0 && this.props.motd && <div className="uk-badge uk-badge-warning "> {motd} </div>}
          <ul className={domstyle}>{exercises}</ul>
          <dl className="uk-description-list-horizontal uk-padding-remove uk-margin-remove">
            {children.map((child) => {
              var folderPrename = child.name.split('.')[0].split(':');
              var folderName = folderPrename[folderPrename.length - 1];
              var selected = this.props.selectedExercises.length > 0;
              var folderClass = child.folded
                ? 'uk-icon-folder uk-margin-small-left'
                : 'uk-icon-folder-open uk-margin-small-left';
              var summaryReq = this.countFinished(child.folder, child.name, 'required');
              if (summaryReq.total > 0) {
                var percentReq = (100 * summaryReq.correct) / summaryReq.total;
              }
              var summaryBonus = this.countFinished(child.folder, child.name, 'bonus');
              if (summaryBonus.total > 0) {
                var percentBonus = (100 * summaryBonus.correct) / summaryBonus.total;
              }
              if (this.props.author) {
                var rendered = [
                  <dt
                    className={foldertext}
                    style={{ float: 'none', overflow: 'visible', width: 'auto' }}
                    key={'dt' + child.name}
                  >
                    <div
                      className="uk-position-relative uk-display-inline"
                      data-uk-dropdown="{hoverDelayIdle: 0, delay: 1000, pos: 'right-center'}"
                    >
                      {author && organize && (
                        <FolderButtonCapture key={nextUnstableKey()} folderName={folderName} folderPath={child.path}>
                          <button
                            className={'uk-icon uk-icon-reply uk-margin-small-left'}
                            data-uk-tooltip="{delay:3000}"
                            title={leftmessage}
                          />
                        </FolderButtonCapture>
                      )}
                      {organize && selected && (
                        <button
                          key={nextUnstableKey()}
                          style={{ color: 'rgb(255,131,0)' }}
                          data-uk-tooltip="{delay:3000}"
                          title={rightmessage}
                          className={'uk-icon uk-icon-arrow-right uk-margin-small-left'}
                          onMouseDown={(e) =>
                            this.props.onFolderRightClick(
                              e,
                              child.path,
                              this.props.selectedExercises,
                              this.props.activeCourse
                            )
                          }
                        />
                      )}

                      <span
                        key={nextUnstableKey()}
                        onClick={(e) => this.props.onFolderLeftClick(e, child.path, child.folded)}
                        tabIndex={-1}
                      >
                        <i key={nextUnstableKey()} className={'uk-icon ' + folderClass} />
                        {folderName === 'Trash' && <i className="uk-icon uk-icon-trash uk-margin-small-left" />}
                        <span className="uk-margin-small-left uk-text-primary">
                          <T>{folderName}</T>
                          {child.pending && <Spinner size="" title="Spinner2" />}
                          {child.pending === null && <i className="uk-icon uk-icon-exclamation-triangle" />}
                        </span>

                        <div
                          className="uk-dropdown uk-dropdown-small uk-margin-small"
                          style={{
                            minWidth: 0,
                            paddingLeft: '5px',
                            paddingRight: '5px',
                            paddingTop: 0,
                            paddingBottom: 0
                          }}
                        ></div>
                      </span>
                    </div>
                  </dt>
                ];
              } else {
                var rendered = [
                  <dt
                    className={foldertext}
                    style={{ float: 'none', overflow: 'visible', width: 'auto' }}
                    key={'dt' + child.name}
                  >
                    <div
                      className="uk-position-relative uk-display-inline"
                      data-uk-dropdown="{hoverDelayIdle: 0, delay: 1000, pos: 'right-center'}"
                    >
                      <span
                        key={nextUnstableKey()}
                        onClick={(e) => this.props.onFolderLeftClick(e, child.path, child.folded)}
                      >
                        <i key={nextUnstableKey()} className={'uk-icon ' + folderClass} />
                        <span className="uk-margin-small-left uk-text-primary">
                          <T>{folderName}</T>
                          {child.pending && <Spinner size="" title="Spinner2" />}
                          {child.pending === null && <i className="uk-icon uk-icon-exclamation-triangle" />}
                        </span>
                      </span>
                    </div>
                  </dt>
                ];
              }
              if (!child.folded) {
                rendered.push(
                  <dd className="uk-margin-left" key={'dd' + child.name}>
                    {' '}
                    {child.content}{' '}
                  </dd>
                );
              }
              return rendered;
            })}
            {level == 0 && createnew && organize && selected && (
              <dt
                className={foldertext}
                style={{ float: 'none', overflow: 'visible', width: 'auto' }}
                key={'dt newew '}
              >
                <div
                  className="uk-position-relative uk-display-inline"
                  data-uk-dropdown="{hoverDelayIdle: 0, delay: 1000, pos: 'right-center'}"
                >
                  <FolderButtonCapture key={nextUnstableKey()} folderName={new_folder} folderPath={['']}>
                    <button
                      className={'uk-icon uk-icon-mail-reply uk-margin-small-left'}
                      data-uk-tooltip="{delay:3000}"
                      title={leftmessage}
                    />
                  </FolderButtonCapture>

                  <span key={nextUnstableKey()} onClick={(e) => this.props.onFolderLeftClick(e, new_folder, false)}>
                    <i
                      key={nextUnstableKey()}
                      style={{ color: 'rgb(255,131,0)' }}
                      className={'uk-icon uk-icon-mail-forward uk-margin-small-left'}
                      data-uk-tooltip="{delay:3000}"
                      title={rightmessage}
                      onClick={(e) =>
                        this.props.onFolderRightClick(
                          e,
                          [new_folder],
                          this.props.selectedExercises,
                          this.props.activeCourse
                        )
                      }
                    />
                    <i key={nextUnstableKey()} className={'uk-icon uk-icon-folder uk-margin-small-left'} />

                    <span className="uk-margin-small-left uk-text-primary">
                      <T>{new_folder_name}</T>
                    </span>
                  </span>
                </div>
              </dt>
            )}
          </dl>
        </div>
      </div>
    );
    return (
      <div>
        {' '}
        {DOMSUMMARY} {DOM}{' '}
      </div>
    );
  };

  render() {
    {
      /* if ( this.props.pendingState.getIn(['course'], false ) ){
      var spinners =  this.props.pendingState.getIn(['course'],[]) 
      for( let[key,value] of spinners ){
          if( true === value ){
              return <Spinner title={key}  msg={key} />;
          }
      }
    }
  
        
  if ( this.props.pendingState.getIn(["course", "loadingExercises"], false)) {
    return <Spinner title='IF THIS KEEPS SPINNING, DISABLE THIRD PARTY COOKIES AND  UNSELECT CROSS-SITE TRACKING' msg={'loadingExercises'} />;
  }
  if (false && this.props.pendingState.getIn(['course', 'loadingExerciseTree'], false)) {
      return (<Spinner title='Spinner4' msg={'loading exercise tree'}  />);
  }
  
  */
    }
    if (this.props.exercisetree) {
      //var foldernames =  ( ( ( this.props.exercisetree.getIn(['folders'],[]  ) ).map( child => child.folder) )._root.entries ).filter( a => a[0]  == new_folder )
      //var createnew = ( foldernames.length < 1 )
      //console.log("FOLDERNAMES1  = " , foldernames.length , createnew )
      var top = this.parseFolder(this.props.exercisetree, '', 0, this.props.displaystyle);
      return (
        <div className="uk-content-center">
          <ul className="uk-list">{top} </ul>
        </div>
      );
    } else {
      return <Spinner title="Spinner5" />;
    }
  }
}

const handleAddExercise = (path) => (dispatch) => {
  return dispatch(fetchAddExercise(path));
};

const mapStateToProps = (state) => ({
  exerciseState: state.get('exerciseState'),
  pendingState: state.get('pendingState'),
  exercisetree: state.get('exerciseTree'),
  exerciseTreeUI: state.get('exerciseTreeUI'),
  displaystyle: state.get('displaystyle'),
  exercisefilter: state.getIn(['exercisefilter'], {
    published_exercises: true,
    all_exercises: false,
    unpublished_exercises: true,
    required_exercises: true,
    optional_exericses: true,
    bonus_exercises: true,
    organize: false
  }),
  lang: state.getIn(['lang']),
  currentpath: state.get('currentpath'),
  showStatistics: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  statistics: state.get('statistics', immutable.Map({})),
  activityRange: state.get('activityRange', '1h'),
  student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  lti_login: state.getIn(['login', 'lti_login'], false),
  activeCourse: state.get('activeCourse'),
  selectedExercises: state.getIn(['selectedExercises'], []),
  subdomain: state.getIn(['login', 'subdomain']),
  motd: state.getIn(['courses', state.get('activeCourse'), 'motd'], '')
});

const mapDispatchToProps = (dispatch) => ({
  onDefaultExerciseClick: (exercise, subdomain) => {
    dispatch(updatePendingStateIn(['exerciseList'], true));
    dispatch(fetchExerciseRemoteState(exercise))
      .then(dispatch(fetchExercise(exercise, true)))
      .then(dispatch(navigateMenuArray(['activeExercise'])));
    dispatch(updateExercises([], subdomain));
    dispatch(fetchSameFolder(exercise, subdomain));
  },

  //onExerciseClickFromResultsView: (exercise,folder) =>  {
  //  dispatch(setDetailResultExercise(exercise));
  //  dispatch(fetchExercise(exercise, true));
  // },

  onChangeView: (view) => dispatch(setDetailResultsView(view)),
  onFolderLeftClick: (e, path, folded) => {
    var fullPath = immutable.List(path).push('$folded$');
    var updated = immutable.Map({}).setIn(fullPath, !folded);
    dispatch(updateExerciseTreeUI(updated));
  },
  onFolderRightClick: (e, path, exercises, coursePk, folded) => {
    var target_path = '/' + path.join('/');
    // console.log("onFolderRightClick target path = ", '/' + path.join('/')  )
    dispatch(fetchMoveExercise(exercises, target_path))
      .then(() => dispatch(fetchExerciseTree(coursePk)))
      .catch((err) => {
        console.dir(err);
      });
    dispatch(resetSelectedExercises());
  },

  onReset: () => {
    dispatch(resetSelectedExercises());
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourse);
