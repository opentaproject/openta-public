import React from 'react';
import { connect } from 'react-redux';

import { updateExerciseTreeUI, updateExerciseState } from '../actions.js';

import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import SafeImg from './SafeImg.jsx';

import immutable from 'immutable';
import moment from 'moment';
import { SUBPATH } from '../settings.js';

function generateItem(
  onExerciseClick,
  exercise,
  exerciseState,
  metaImmutable,
  folder,
  foldername,
  showStatistics,
  statistics,
  activityRange,
  author
) {
  var meta = metaImmutable.toJS();
  var deadlineClass = 'uk-badge-primary';
  var legend = 'Obligatorisk';
  if (meta.bonus) {
    deadlineClass = 'uk-badge-warning';
    legend = 'Bonus';
  }
  var selectedStyle = {};
  if (exerciseState.getIn([exercise, 'selected'])) {
    selectedStyle = {
      borderColor: 'rgb(0,221,0)',
      borderWidth: '4px',
      borderStyle: 'solid'
    };
  }

  var thumbnail = meta.thumbnail
  return (
    <li key={exercise} id={exercise} className="course-exercise-item ">
      <div className="uk-position-relative" data-uk-dropdown="{hoverDelayIdle: 0, delay: 300}">
        <a
          className={'uk-thumbnail exercise-a ' + (meta.published ? '' : 'exercise-unpublished')}
          onClick={(ev) =>
            onExerciseClick(exercise, foldername, folder.get('path'), exerciseState.getIn([exercise, 'selected']))
          }
          style={selectedStyle}
        >
          <div className="exercise-thumb-wrap" style={{ minWidth: '80px' }}>
            <SafeImg className="exercise-thumb-nav" src={SUBPATH + '/exercise/' + exercise + '/asset/' + thumbnail }>
              <i className="uk-icon uk-icon-question-circle uk-icon-large" />
            </SafeImg>
            <div className="exercise-thumb-badge">
              {meta.deadline_date && (
                <Badge className={'uk-badge-notification ' + deadlineClass} title={legend}>
                  {moment(meta.deadline_date).format('D MMM')}
                </Badge>
              )}
              {meta.image && (
                <span className={'uk-badge uk-badge-notification '}>
                  <i className="uk-icon uk-icon-camera" />
                </span>
              )}
              {meta.solution && <Badge className={'uk-badge-notification'}>lösning</Badge>}
            </div>
          </div>
          <div className={'uk-thumbnail-caption exercise-thumb-nav-caption '}>
            {folder.getIn(['exercises', exercise, 'name'])}
          </div>
        </a>
      </div>
    </li>
  );
}

const BaseExerciseSelect = ({
  exercisetree,
  exerciseTreeUI,
  exerciseState,
  pendingState,
  currentpath,
  onExerciseClick,
  view,
  admin,
  statistics,
  activityRange,
  onFolderClick,
  student,
  author
}) => {
  var showStatistics = view || admin || author;
  function parseFolder(folder, foldername, level = 0) {
    var exercises = immutable.List([]),
      children = [];
    if (folder.has('exercises')) {
      exercises = folder
        .get('order')
        .filter((exercise) => folder.getIn(['exercises', exercise, 'meta', 'published']))
        .map((exercise) => {
          var meta = folder.getIn(['exercises', exercise, 'meta']);
          return generateItem(
            onExerciseClick,
            exercise,
            exerciseState,
            meta,
            folder,
            foldername,
            showStatistics,
            statistics,
            activityRange,
            author
          );
        });
    }
    if (folder.has('folders')) {
      children = folder
        .get('folders', immutable.Map({}))
        .keySeq()
        .sort()
        .map((childfolder) => ({
          name: childfolder,
          folder: folder.getIn(['folders', childfolder, 'content']),
          content: parseFolder(folder.getIn(['folders', childfolder, 'content']), childfolder, level + 1),
          path: folder.getIn(['folders', childfolder, 'content', 'path']),
          folded: exerciseTreeUI.getIn(
            folder.getIn(['folders', childfolder, 'content', 'path']).push('$folded$'),
            false
          ),
          pending: exerciseTreeUI.getIn(
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
    var DOM = (
      <div className={'uk-block uk-padding-remove ' + levelClass}>
        <div className="uk-container uk-margin-small-left uk-margin-small-right uk-padding-remove">
          <ul className="uk-thumbnav uk-flex uk-flex-bottom uk-padding-remove">{exercises}</ul>
          <dl className="uk-description-list-horizontal">
            {children.map((child) => {
              var folderPrename = child.name.split('.')[0].split(':');
              var folderName = folderPrename[folderPrename.length - 1];
              var folderClass = child.folded ? 'uk-icon-folder' : 'uk-icon-folder-open';
              var rendered = [
                <dt
                  className="uk-text-large uk-margin-right"
                  style={{ float: 'none', overflow: 'visible', width: 'auto' }}
                  key={'dt' + child.name}
                >
                  <div
                    className="uk-position-relative uk-display-inline"
                    data-uk-dropdown="{hoverDelayIdle: 0, delay: 300, pos: 'right-center'}"
                  >
                    <a onClick={() => onFolderClick(child.path, child.folded)}>
                      <i className={'uk-icon ' + folderClass} />
                      {folderName === 'Trash' && <i className="uk-icon uk-icon-trash uk-margin-small-left" />}
                      <span className="uk-margin-small-left">
                        {folderName}
                        {child.pending && <Spinner size="" />}
                        {child.pending === null && <i className="uk-icon uk-icon-exclamation-triangle" />}
                      </span>
                    </a>
                  </div>
                </dt>
              ];
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
          </dl>
        </div>
      </div>
    );
    return DOM;
  }
  if (pendingState.getIn(['course', 'loadingExercises'], false)) {
    return <Spinner />;
  }
  if (exercisetree) {
    var top = parseFolder(exercisetree, '/');
    return (
      <div className="uk-content-center">
        <ul className="uk-list">{top}</ul>
      </div>
    );
  } else {
    return <Spinner />;
  }
};

const mapStateToProps = (state) => ({
  exerciseState: state.get('exerciseState'),
  pendingState: state.get('pendingState'),
  exercisetree: state.get('exerciseTree'),
  exerciseTreeUI: state.get('exerciseTreeUI'),
  currentpath: state.get('currentpath'),
  statistics: state.get('statistics', immutable.Map({})),
  student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin')
});

const mapDispatchToProps = (dispatch) => ({
  onExerciseClick: (exercise, folder, folderpath, selected) => {
    dispatch(updateExerciseState(exercise, immutable.Map({ selected: !selected })));
  },
  onFolderClick: (path, folded) => {
    var fullPath = immutable.List(path).push('$folded$');
    var updated = immutable.Map({}).setIn(fullPath, !folded);
    dispatch(updateExerciseTreeUI(updated));
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseSelect);
