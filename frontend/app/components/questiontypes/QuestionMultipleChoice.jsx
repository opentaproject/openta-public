/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { Component } from "react"; // React specific import
import PropTypes from "prop-types";
import T from "../Translation.jsx";
import t from '../../translations.js';

import { registerQuestionType } from "./question_type_dispatch.js"; // Register function used at the bottom of this file to let the system know of the question type
import Alert from "../Alert.jsx"; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import SafeMathAlert from "../SafeMathAlert.jsx"; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from "../Badge.jsx"; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpMultipleChoice from "./HelpMultipleChoice.jsx";
import MathSpan from "../MathSpan.jsx";
import immutable from "immutable";
import { SUBPATH } from "../../settings.js";
import DOMPurify from "dompurify";
import { renderText  } from "./render_text.js"


/* 
 *
 THIS renderText is all that is left; it renders text only in choices and has restricted functionality

 */






export default class QuestionMultipleChoice extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool, //Indicates if user is allowed to see solution.
    exerciseKey: PropTypes.string //Exercise key
  };

  constructor(props) {
    super(props);
    this.state = {
      choices: immutable.fromJS(JSON.parse(this.props.questionState.getIn(["answer"], "{}")))
    };
  }

  toggleChoice = choice => {
    this.setState(({ choices }) => ({ choices: choices.update(choice, v => !v) }));
  };

  renderFigure = itemjson => {
    return (
      <a
        key={"figure" + itemjson.get("$")}
        href={SUBPATH + "/exercise/" + this.props.exerciseKey + "/asset/" + itemjson.get("$")}
        data-uk-lightbox
        data-lightbox-type="image"
      >
        <img
          style={{ maxHeight: "100pt" }}
          src={SUBPATH + "/exercise/" + this.props.exerciseKey + "/asset/" + itemjson.get("$")}
          alt=""
        />
      </a>
    );
  };
  renderAsset = itemjson => {
    return (
      <a
        key={"asset" + itemjson.get("$")}
        className="uk-button uk-button-small"
        href={SUBPATH + "/exercise/" + this.props.exerciseKey + "/asset/" + itemjson.get("$")}
      >
        {itemjson.getIn(["@attr", "name"])}
      </a>
    );
  };

  dispatchElement = element => {
    var itemDispatch = {
      text: itemjson => renderText(itemjson, self.dispatchElement, this.props.lang),
      __text__: itemjson => renderText(itemjson, self.dispatchElement, this.props.lang),
      alt: itemjson => renderText(itemjson, self.dispatchElement, this.props.lang),
      figure: this.renderFigure,
      asset: this.renderAsset
    };
    if (element.get("#name") in itemDispatch) return itemDispatch[element.get("#name")](element);
    else return null;
  };

  renderContentInPanel = (element, badge) => {
    var children = element
      .get("$children$", immutable.List([]))
      .map(child => this.dispatchElement(child))
      .toSeq();
    return (
      <div className="uk-panel uk-panel-box uk-margin-bottom">
        <div className="uk-panel-badge">{badge}</div>
        {children}
        <MathSpan>{element.get("$")}</MathSpan>
      </div>
    );
  };

  render() {
    // Some convenience definitions
    var question = this.props.questionData;
    var state = this.props.questionState;
    var submit = this.props.submitFunction;
    var pending = this.props.questionPending;
    var unchecked = '('+t('unchecked')+')';
    var questiontext = this.props.renderText(question.getIn(['text']));
    if (state.getIn(["response", "question"])) {
      question = state.getIn(["response", "question"]);
    }
    /*
     * Both the questionData and questionState are of type Map from immutable.js.
     * They are nested dictionaries that are accessed via the get and getIn
     * functions. For example question.get('text') retrieves <question> <text> *
     * </text> </question>. Deeper structures can be accessed with getIn, for
     * example question.getIn(['tag1', 'tag2']) would retrieve <question> <tag1>
     * <tag2> * </tag2> </tag1> </question>.
     */

    // System state data
    var lastAnswer = JSON.parse(state.getIn(["answer"], "{}")); // Last saved answer in database, same format as passed to the submitFunction
    var correctAnswers = state.getIn(["response", "choices"], immutable.Map({}));
    var correct = state.getIn(["response", "correct"], false) || state.getIn(["correct"], false); // Boolean indicating if the grader reported correct answer
    var n_attempts = state.getIn(["response", "n_attempts"], question.getIn(["n_attempts"]), 0);
    if (state.getIn(['correct'], null) == null) {
      var feedback = false
    } else {
      var feedback = true
    }

    var choicesElements = question.get("choice", immutable.List([]));
    if (choicesElements.length > 1) {
      choicesElements = choicesElements.sort((a, b) => {
        var x = a.getIn(["@attr", "order"], 0);
        var y = b.getIn(["@attr", "order"], 0);
        return x < y ? -1 : x > y ? 1 : 0;
      });
    }

    if (!immutable.List.isList(choicesElements))
      choicesElements = immutable.List([choicesElements]);
    var choices = choicesElements.map((item, key) => {
      var style = {};
      var choiceKey = item.getIn(["@attr", "key"], "index_" + key);
      var divClass = this.state.choices.get(choiceKey) ? "uk-panel-box-primary" : "";
      var children = item
        .get("$children$", immutable.List([]))
        .map(child => this.dispatchElement(child))
        .toSeq();
      var duplicateKey =
        choicesElements.filter(item => item.getIn(["@attr", "key"]) === choiceKey).size > 1;
      var reactKey = duplicateKey ? choiceKey + key : choiceKey;
      return (
        <div className="uk-width-1-1" key={reactKey}>
          <div
            style={style}
            className={"uk-panel uk-panel-box uk-margin-bottom pointer mc-item " + divClass}
            onClick={() => this.toggleChoice(choiceKey)}
          >
            <div className="uk-panel-badge">
              {feedback && lastAnswer[choiceKey] && (
                <div className="uk-margin-small-left uk-display-inline-block ">
                  <i className="uk-margin-small-top uk-icon uk-icon-check-square-o" />
                </div>
              )}
              {feedback && !lastAnswer[choiceKey] && (
                <div className="uk-margin-small-left uk-display-inline-block ">
                  <i className="uk-margin-small-top uk-icon uk-icon-square-o" />
                </div>
              )}
              { feedback && this.props.canViewSolution && item.getIn(["@attr", "correct"]) === "true" && (
                <div className="uk-margin-small-left uk-margin-small-right uk-badge">correct</div>
              )}
              {this.props.isAuthor && <div className="uk-badge">{choiceKey}</div>}
              {feedback && correctAnswers.get(choiceKey) && (
                <div className="uk-margin-small-left uk-margin-small-right uk-badge uk-badge-success">
                  <T>Correct!</T>
                </div>
              )}
              {feedback &&
                correctAnswers.get(choiceKey) === false &&
                lastAnswer[choiceKey] === true && (
                  <div className="uk-margin-small-left uk-margin-small-right uk-badge uk-badge-danger">
                    <T>Incorrect</T>
                  </div>
                )}
              {item.hasIn(["@attr", "key"]) && duplicateKey && (
                <div className="uk-margin-small-right uk-badge uk-badge-danger">
                  Duplicate choice key!
                </div>
              )}
              {!item.hasIn(["@attr", "key"]) && (
                <div className="uk-margin-small-left uk-margin-small-right uk-badge uk-badge-warning">
                  No choice key, please add an attribute key="..."{" "}
                </div>
              )}
              {this.state.choices.get(choiceKey) && (
                <div className="uk-margin-small-left uk-display-inline-block">
                  <i className="uk-margin-small-top uk-icon uk-icon-medium uk-icon-check-square-o" />
                </div>
              )}
              {!this.state.choices.get(choiceKey) && (
                <div className="uk-margin-small-left uk-display-inline-block">
                  <i className="uk-margin-small-top uk-icon uk-icon-medium uk-icon-square-o" />
                </div>
              )}
            </div>
            {children}
          </div>
        </div>
      );
    });

    // Custom state data
    var error = state.getIn(["response", "error"]); // Custom field containing error information
    var author_error = state.getIn(["response", "author_error"]); // Custom field containing error information
    var info = state.getIn(["response", "info"]); // Custom field containing error information
    var stick =
      n_attempts > 4 && n_attempts % 2 == 0
        ? " ( " + n_attempts + " attempts): are you guessing?"
        : " ( " + n_attempts + " attempts. )";
    var carrot =
      ( n_attempts < 2  &&  feedback ) ? " On the first attempt. Good work!" : " Number of attempts =  " + n_attempts;
    return (
      <div className="">
        <label className="uk-form-row uk-display-inline-block uk-margin-bottom">
          {questiontext} <HelpMultipleChoice />
        </label>
      { ! this.props.locked && (
        <a
          onClick={event => submit(JSON.stringify(this.state.choices))}
          className={"uk-width-1-1 uk-button uk-padding-remove uk-button-success uk-margin-bottom"} >
          {pending && <i className="uk-icon-cog uk-icon-spin" />}
          {!pending && <i className="uk-icon uk-icon-send" />}
        </a>
        ) }
        {feedback && correct && (
          <Alert className="uk-margin-small-top uk-margin-small-bottom" type="success" key="input">
            {" "}
            Correct! {carrot}{" "}
          </Alert>
        )}
        {!feedback &&
          (
            <Alert className="uk-margin-small-top uk-margin-small-bottom" type="primary" key="input">
              {" "}
              {unchecked} {stick}{" "}
            </Alert>
          )}
        {feedback && n_attempts > 0 && !correct && (
          <Alert className="uk-margin-small-top uk-margin-small-bottom" type="error" key="input">
            {" "}
            Not correct {stick}{" "}
          </Alert>
        )}
        {error && <Alert message={error} type="error" key="err" />}
        {author_error && this.props.isAuthor && (
          <Alert message={author_error} type="error" key="author_error" />
        )}
        {info && <Alert message={info} type="info" key="info" />}
        {feedback && question.has("hint") &&
          !correct &&
          state.get("answer", "") !== "" &&
          this.renderContentInPanel(question.get("hint"), <div className="uk-badge">Hint</div>)}
        <div className="uk-grid uk-grid-small">{choices}</div>
      </div>
    );
  }
}

//Register the question component with the system
registerQuestionType("multipleChoice", QuestionMultipleChoice);
