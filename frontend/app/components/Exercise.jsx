"use strict";
import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import Question from './Question.jsx';
import QMath from './QMath.jsx';
import AsciiMath from './AsciiMath.jsx';
import Spinner from './Spinner.jsx';
import immutable from 'immutable';
import moment from 'moment';
import DOMPurify from 'dompurify';
import ExerciseImageUpload from './ExerciseImageUpload.jsx';
import T from './Translation.jsx';
import Badge from './Badge.jsx';
import Assets from './Assets.jsx';
import {SUBPATH} from '../settings.js';
import classNames from 'classnames';
import uniqueId from 'lodash/uniqueId';
import { navigateMenuArray } from '../menu.js';



import {
  updateExerciseXML,
  updateExerciseJSON,
  setExerciseModifiedState
} from '../actions.js';
import {
  saveExercise,
  fetchExercise,
  checkQuestion,
  fetchAssets
} from '../fetchers.js';

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

class BaseExercise extends Component {
  constructor() {
    super();
    this.itemDispatch = {
      'exercisename': this.renderName,
      'text': this.renderText,
      'figure': this.renderFigure,
      'question': this.renderQuestion,
      'qmath': this.renderQuestionMath,
      'asciimath': this.renderAsciiMath,
      'solution': this.renderSolution,
      'hidden': this.renderHidden,
      'asset': this.renderAsset,
      'p': this.renderHTMLElement(),
      'i': this.renderHTMLElement(),
      'b': this.renderHTMLElement(),
      'strong': this.renderHTMLElement(),
      'em': this.renderHTMLElement(),
      'pre': this.renderTag("<pre>", "</pre>"),
      'code': this.renderTag("<pre><code>", "</code></pre>"),
      'h3': this.renderHTMLElement(),
      'h2': this.renderHTMLElement(),
      'h1': this.renderHTMLElement(),
      'hr': this.renderHTMLElementHR(),
      'br': this.renderHTMLElementBR(),
      'ul': this.renderHTMLElement("uk-list"),
      'li': this.renderHTMLElement(),
      'table': this.renderHTMLElement(),
      'tr': this.renderHTMLElement(),
      'thead': this.renderHTMLElement(),
      'tbody': this.renderHTMLElement(),
      'td': this.renderHTMLElement(),
      'th': this.renderHTMLElement(),
      'a': this.renderHTMLElementA(),
      'right': this.renderRight,
      '__text__': this.renderBareText,
      'alt': this.renderText,
    };
  }

  static propTypes = {
    admin: PropTypes.bool,
    exerciseKey: PropTypes.string.isRequired,
    onQuestionInputKeyUp: PropTypes.func,
    exerciseState: PropTypes.object,
    pendingState: PropTypes.object,
    onHome: PropTypes.func,
    locked: PropTypes.bool
  };

  renderQuestion = (itemjson, json, meta, exerciseKey) => {
    var questions = json.getIn(['exercise', 'question'], immutable.List([]));
    var question = itemjson;
    var questionRenderText = (itemjson) => this.renderText(itemjson, json, meta, exerciseKey)
    var locked = this.props.locked && ! this.props.author
    return (
          <div key={"q" + question.getIn(['@attr', 'key'])}>
          { questions.filter( q => q.getIn(['@attr','key']) == question.getIn(['@attr','key']) ).count() > 1 && this.props.admin && <Alert message="Duplicate question keys! (If you copied a question please change the key attribute)" type="error"/> }
          <form key={question.getIn(['@attr','key'])} className="uk-form" onSubmit={(event) => event.preventDefault()}>
          {<Question exerciseKey={exerciseKey} locked={locked} renderText={questionRenderText} questionKey={question.getIn(['@attr','key'])}/>}
          </form>
          </div>
            );
  }

  renderTag = (tagopen='<pre>', tagclose='</pre>', extraAttrs=[] )  => (itemjson, json, meta, exerciseKey) => {
          var children = itemjson.get('$children$', immutable.List([]))
                    .filter(item => item.get('#name') === 'figure')
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <span className="uk-clearfix" key={"text"}>
      <span className="uk-align-right">{children}</span>
      <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(tagopen + itemjson.get('$') + tagclose)}} />
      </span>
    );
  }


  renderQuestionMath = (itemjson, json, meta, exerciseKey) => {
    var question = itemjson;
    var type =  question.getIn(['@attr','type'], 'devLinearAlgebra')
    return (
      <span key={"qmath" + nextUnstableKey()}>
        <QMath exerciseKey={exerciseKey} questionType={type} expression={itemjson.get('$', '')}/>
      </span>
    );
  }

  renderAsciiMath = (itemjson, json, meta, exerciseKey) => {
    return (
      <span key={"asciimath" + nextUnstableKey()}>
        <AsciiMath>{itemjson.get('$', '')}</AsciiMath>
      </span>
    );
  }

  renderLegacyText = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .filter(item => item.get('#name') === 'figure')
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <div className="uk-clearfix" key={"text"}>
      <div className="uk-align-medium-right">{children}</div>
      <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(itemjson.get('$'))}} />
      </div>
    );
  }

  filterLanguage = (children) => {
    var filtered = children.filter(item => item.getIn(['@attr', 'lang'], undefined) === this.props.language);
    if(filtered.size > 0) {
      return filtered;
    }
    else {
      return children.filter(item => !item.hasIn(['@attr', 'lang']));
    }
  }

  renderText = (itemjson, json, meta, exerciseKey) => {
    if (itemjson ){
    var childrenList = this.filterLanguage(itemjson.get('$children$', immutable.List([])));

    if(childrenList.filter( item => item.get('#name','') === 'figure').size == 1 &&
        childrenList.size == 2)
      return this.renderLegacyText(itemjson, json, meta, exerciseKey);
    var children =  childrenList
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <div className="uk-clearfix" key={"text" + nextUnstableKey()}>
        {children}
      </div>
    );
    } else {
    return (<Badge className={"uk-badge uk-text-medium uk-badge-danger"} > Text missing ! </Badge> )
    }
  }

  renderFigure = (itemjson, json, meta, exerciseKey) => {
    var figure = itemjson.get('$', '');
    var size = itemjson.getIn(['@attr', 'size'], 'small');
    var sizeClass = {
      "uk-thumbnail": true,
      "uk-thumbnail-small": size == 'small' || !(size in ['small', 'medium', 'large']),
      "uk-thumbnail-medium": size == 'medium',
      "uk-thumbnail-large": size == 'large',
    }

      return (
        <a className={classNames(sizeClass)} key={"figure"+figure} href={SUBPATH + '/exercise/' + exerciseKey + '/asset/' + figure.trim()} data-uk-lightbox data-lightbox-type="image">
          <img src={SUBPATH + '/exercise/' + this.props.exerciseKey + '/asset/' + figure.trim()} alt=""/>
          { itemjson.has('caption') && <div className="uk-thumbnail-caption">{itemjson.getIn(['caption', '$'])}</div> }
        </a>
      );
  }

  renderSolution = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    var canViewXML =  this.props.author || this.props.view
    return (
      <div className="uk-margin-bottom uk-text-center" key={"solution"}>
      { meta.get('solution', false) && children }

      {!meta.get('solution', false) && this.props.view &&
        <div className="uk-block uk-block-muted uk-padding-remove uk-text-warning">
          Dold för studenter.
          { canViewXML && <span>Visa för studenter genom att klicka i "solution" i inställningarna.</span>}
        </div> }
      {!meta.get('solution', false) && this.props.view && <div className="uk-block uk-block-muted uk-padding-remove">{children}</div>}
      </div>
    );
  }


renderHidden = (itemjson, json, meta, exerciseKey) => {
    var label = itemjson.getIn(['@attr','label'], "hidden")
    var children = itemjson.get('$children$', immutable.List([]))
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    var style='uk-icon uk-icon-medium uk-text-primary uk-text-small uk-icon-life-ring uk-margin-small-left uk-text-middle'
    var subClass = 'uk-hidden uk-text-muted uk-background-secondary uk-text-small'
    var labelClass = 'uk-padding uk-padding-remove-vertical uk-text-danger'
    var id = uniqueId('hiddenItem');
    if(this.props.view) {
      return <span key={id}>
          <a className="uk-button  uk-button-link" data-uk-toggle={"{target:'#" + id + "'}"}>
            <i className={style} />
            <span className={labelClass}> {label} </span>{" "}
          </a>
          <div id={id} className={subClass}>
            <div className="uk-margin-bottom uk-text-left uk-panel uk-panel-box uk-panel-box-primary" key={"hidden"}>
              { children }
            </div>
          </div>
        </span>;
    }
    else {
      return <span/>;
    }
  }


  renderAsset = (itemjson, json, meta, exerciseKey) => {
    return (
      <a key={"asset" + itemjson.get('$')} className="uk-button uk-button-small" target="_blank" href={SUBPATH + '/exercise/' + exerciseKey + '/asset/' + itemjson.get('$','').trim()}>{itemjson.getIn(['@attr', 'name'])}</a>
    );
  }

  renderName = (itemjson, json, meta, exerciseKey) => {
    var deadlineDate = meta.get('deadline_date');
    var deadlineTime = meta.get('deadline_time');
    var deadlineDateFormat = '';
    if(deadlineDate) {
        if(deadlineTime)
            deadlineDateFormat = moment(deadlineDate + ' ' + deadlineTime).format('D MMM HH:mm');
        else
            deadlineDateFormat = moment(deadlineDate).format('D MMM');
    }
    var obligatorisk = meta.get('required', false);
    var bonus = meta.get('bonus', false);
    var translations = this.filterLanguage(itemjson.get('$children$', immutable.List([])));
    var name = itemjson.get('$');
    var canViewXML =  this.props.author || this.props.view
    if(translations.size > 0)
      name = translations.first().get('$');

    return (
      <div key="name">
      <h1 className="uk-article-title">{name}
      { deadlineDate && <div className="uk-badge uk-badge-danger uk-margin-small-left">
        <a data-uk-tooltip title="Du kan fortfarande kontrollera svar efter deadline men de kommer inte räknas mot obligatorisk/bonus.">
          Deadline: {deadlineDateFormat}
          <i className="uk-icon uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a>
      </div>}
      { deadlineDate && obligatorisk && <div className="uk-badge uk-margin-small-left">Obligatorisk</div>}
      { deadlineDate && bonus && <div className="uk-badge uk-badge-warning uk-margin-small-left">Bonus</div>}
      { canViewXML && !meta.get('published') && <div className="uk-badge uk-badge-danger uk-margin-small-left"><T>Unpublished</T></div> }
          </h1>
          </div>
    );
  }

    renderHTMLElementA = () =>  (itemjson, json, meta, exerciseKey) => {
        var children = itemjson.get('$children$', immutable.List([]))
                               .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toList();
        return (<a href={itemjson.getIn(['@attr', 'href'])} target="_blank" key={nextUnstableKey()}>{children}</a>)
    }

    renderHTMLElementHR = () =>  (itemjson, json, meta, exerciseKey) => {
        return (<div key={nextUnstableKey()}> <hr/> </div> )
    }

    renderHTMLElementBR = () =>  (itemjson, json, meta, exerciseKey) => {
        return (<div key={nextUnstableKey()}> <br/> </div> )
    }

    renderHTMLElement = (className="", extraAttrs=[]) => (itemjson, json, meta, exerciseKey) => {
        var attrs = {};
        for(let attr of extraAttrs)
            attrs[attr] = itemjson.getIn(['@attr', attr])

        var children = itemjson.get('$children$', immutable.List([]))
                               .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toList();
        var itemDOM = React.createElement(itemjson.get('#name'), {
            className: className + " " + itemjson.getIn(['@attr', 'class']),
            style: itemjson.getIn(['@attr', 'style']),
            key: nextUnstableKey(),
            ...attrs
        }, children);
        return itemDOM;
    }

  renderBareText = (itemjson, json, meta, exerciseKey) => (<span key={nextUnstableKey()} dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(itemjson.get('$'))}}/>)

  renderRight = (itemjson, json, meta, exerciseKey) => (
    <div className="uk-align-medium-right" key={nextUnstableKey()}>
      {
        itemjson.get('$children$', immutable.List([]))
          .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toList()
      }
    </div>)

  dispatchElement = (element, json, meta, exerciseKey) => {
    if(element.get('#name') in this.itemDispatch)
      return this.itemDispatch[element.get('#name')](element, json, meta, exerciseKey);
    else
      return null;
  }

  basename = (path) =>  {
    if ( ! path == ''  ){
    return path.split('/').reverse()[0];
    } else {
    return ''
    }
  }

  render() {
    var key = this.props.exerciseKey;
    var state = this.props.exerciseState;
    //////////////////
    //var locked = true
    //if ( this.props.exercisemeta.size > 0 ){
    //   var locked = this.props.exercisemeta.first().getIn(['meta'],{} ).getIn(['locked'],true)
    //  }
    var locked = this.props.locked && !this.props.author
    var pendingState = this.props.pendingState;
    var filename = this.basename(state.getIn(['path'], '') );
    var json = state.get('json', immutable.Map({}));
    var error = json.get('error', null )
    var response_awaits = Number(state.getIn(["response_awaits"], 0));
    var meta = state.get('meta', immutable.Map({}));
    if(meta === null)meta = immutable.Map({});
    var items = json.getIn(['exercise','$children$'], immutable.List([]))
                    .map( child => this.dispatchElement(child, json, meta, key) ).toSeq();
    var canViewXML =  this.props.author || this.props.view
    var canUpload = ( ! this.props.view ) || this.props.admin || this.props.author
    var showResponseAwaits = response_awaits > 0;
    var filenameDOM = (
      <span className="uk-text-bold uk-text-primary">
        Exercise file path: {filename}
      </span>);
    var exerciseDOM = <div className="uk-width-1-1"> <article className="uk-article uk-margin-top uk-margin-small-right uk-margin-small-left" ref="exercise" key={key}>
        
        {canViewXML && showResponseAwaits && <i className="uk-text-danger uk-margin-small-left uk-icon uk-icon uk-icon-envelope" />}
        {/* <a className="uk-navbar-brand onHome" onClick={this.props.onHome}> <i className="uk-icon uk-icon-tiny uk-icon-mail-reply"></i> </a> */}
        {error && canViewXML && <Alert message={error} type="error" />}
        {canViewXML && filenameDOM}
        { meta.get("student_assets") && <Assets locked={locked}  />}
        {  canUpload && meta.get("image", false) && <div className="uk-float-right uk-margin-small-right">
              <ExerciseImageUpload  locked={locked} />
            </div>}
        {items}
      </article> </div>

    if(pendingState.getIn(['exercises', key, 'loadingJSON'], false)) {
      return (<Spinner/>);
    }
    else
      return exerciseDOM;
  }

  componentDidMount(props, state, root) {
    this.props.getAssets();
    this.componentDidUpdate(props, state, root);
  }
  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.refs.exercise);
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [
          {left: "$", right: "$", display: false},
          {left: "\\[", right: "\\]", display: true}
        ]
      });
  }
}

const mapStateToProps = state => {
  var activeExercise = state.get('activeExercise')
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  var exercisemeta =  ( state.getIn(['exercises'], immutable.List([])).filter( item => ( item.get('exercise_key') == activeExercise) ) )
  var locked = true
  if ( exercisemeta.size > 0 ){
      locked = exercisemeta.first().getIn(['meta'],{} ).getIn(['locked'],true)
      }
  const defaultLanguage = state.getIn(['course', 'languages', 0], 'en');
  return (
  {
    author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
    admin: state.getIn(['login', 'groups'],immutable.List([])).includes('Admin'),
    view: state.getIn(['login', 'groups'],immutable.List([])).includes('View'),
    language: state.get('lang', defaultLanguage),
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState'),
    locked: locked

  })
};

const mapDispatchToProps = dispatch => {
  return {
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question),
    getAssets: () => dispatch(fetchAssets()),
    onHome: () => dispatch(navigateMenuArray([])),
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
