/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { Component } from "react"; // React specific import
import PropTypes from "prop-types";

import { registerQuestionType } from "./question_type_dispatch.js"; // Register function used at the bottom of this file to let the system know of the question type
import Alert from "../Alert.jsx"; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from "../Badge.jsx"; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpPythonic from "./HelpPythonic.jsx";
import T from "../Translation.jsx";
import t from "../../translations.js";
import { throttle } from "lodash";

export default class QuestionPythonic extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool //Indicates if user is allowed to see solution.
  };

  constructor(props) {
    super(props);
    this.state = {
      value: this.props.questionState.getIn(["answer"], ""),
      mathSize: "medium",
      cursor: 0
    };
    this.lastParsable = "";
    if (this.props.canViewSolution)
      this.state.value = this.props.questionData
        .getIn(["expression", "$"], "")
        .replace(/;/g, "")
        .trim();
  }

  handleChange = event => {
    this.setState({ value: event.target.value });
  };

  updateCursor = throttle(pos => {
    this.setState({ cursor: pos });
  }, 500);

  handleSelect = event => {
    this.updateCursor(event.target.selectionStart);
  };

  setMathSize = sizeStr => {
    this.setState({ mathSize: sizeStr });
  };

  componentWillReceiveProps = newProps => {};

  /* render gets called every time the question is shown on screen */
  render() {
    // Some convenience definitions
    var question = this.props.questionData;
    var state = this.props.questionState;
    var submit = this.props.submitFunction;
    var pending = this.props.questionPending;
    var answerbox = question.getIn(["@attr", "answerbox"], true);
    var notanswerbox = false;
    if (answerbox == "false" || answerbox == "False") {
      answerbox = false;
      notanswerbox = true;
    } else {
      answerbox = true;
      notanswerbox = false;
    }

    /* Both the questionData and questionState are of type Map from immutable.js. They are nested dictionaries that are accessed via the get and getIn functions. For example question.get('text') retrieves <question> <text> * </text> </question>. Deeper structures can be accessed with getIn, for example question.getIn(['tag1', 'tag2']) would retrieve <question> <tag1> <tag2> * </tag2> </tag1> </question>. */

    // System state data
    var lastAnswer = state.getIn(["answer"], ""); // Last saved answer in database, same format as passed to the submitFunction
    var correct = state.getIn(["response", "correct"], null) || state.getIn(["correct"], null); // Boolean indicating if the grader reported correct answer
    var correct = state.getIn(["response", "correct"], false) || state.getIn(["correct"], false); // Boolean indicating if the grader reported correct answer
    var n_attempts = state.getIn(["response", "n_attempts"], question.getIn(["n_attempts"]));
    var previous_answers = state.getIn(["response", "previous_answers"], question.getIn(["previous_answers"]));
    // override default true xml of feedback with options
    if (state.getIn(["correct"], null) == null) {
      var feedback = false;
    } else {
      var feedback = true;
    }

    var error = state.getIn(["response", "error"]); // Custom field containing error information
    var author_error = state.getIn(["response", "author_error"]); // Custom field containing error information
    var warning = state.getIn(["response", "warning"]); // Custom field containing error information
    var hint = state.getIn(["response", "hint"]); // Custom field containing error information
    var comment = state.getIn(["response", "comment"], "");
    var tdict = state.getIn(["response", "dict"], "");
    if (state.getIn(["response", "detail"]))
      error =
        "Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)";

    var graderResponse = null;
    var input = this.state.value.trim();
    if (notanswerbox) {
      input = " "; // MAKE THIS A BLANK SO AS NOT TO TRIGGER A NOOP in fetchers.js/questionCheck
    }

    var hasChanged = input !== lastAnswer;
    var nonEmpty = input !== "";
    var unchecked = "(" + t("unchecked") + ")";
    if (notanswerbox || (input === lastAnswer && lastAnswer !== "" && !error)) {
      if (feedback) {
        if (correct) {
          graderResponse = (
            <Alert
              className="uk-margin-small-top uk-margin-small-bottom"
              message={t("Correct") + t(comment, tdict)}
              type="success"
              key="input"
            />
          );
          if (n_attempts < 2) {
            graderResponse = (
              <Alert
                className="uk-margin-small-top uk-margin-small-bottom"
                message={t("Correct first time!") + t(comment, tdict)}
                type="success"
                key="input"
              />
            );
          }
        } else if (correct === null) {
          graderResponse = (
            <Alert
              className="uk-margin-small-top uk-margin-small-bottom"
              message={t("Unchecked")}
              key="input"
            />
          );
        } else {
          graderResponse = (
            <Alert
              className="uk-margin-small-top uk-margin-small-bottom"
              message={t("Not correct.") + t(comment, tdict)}
              type="warning"
              key="input"
            />
          );
          if (n_attempts > 4 && n_attempts % 2 == 0) {
            graderResponse = (
              <Alert
                className="uk-margin-small-top uk-margin-small-bottom"
                message={t("Is not correct.") + t(comment, tdict)}
                type="warning"
                key="input"
              />
            );
          }
        }
      } else {
        graderResponse = (
          <Alert
            className="uk-margin-small-top uk-margin-small-bottom"
            message={unchecked + t(comment, tdict)}
            type="text"
            key="input"
            hasMath={false}
          />
        );
      }
    }
    var itemjson = question.getIn(["text"], undefined);
    var questiontext = this.props.renderText(itemjson)
    var questionkey = question.getIn(['@attr', 'key']);
    var msg1 = "QuestionType QuestionPythonic";
    return (
      <div className="">
        {questiontext}
        <span className="uk-text-small uk-text-primary">
          {" "}
          [ {feedback} {n_attempts} <T>attempts</T> ]{" "}
        </span>

        <HelpPythonic />
        <span data-uk-tooltip title={msg1} />
        {hasChanged && lastAnswer !== "" && (
          <Badge
            message={t("previous") + "  " + lastAnswer}
            hasMath={false}
            className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"
          />
        )}
        <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
            {answerbox && (
              <div className="uk-width-1-1">
                <textarea
                  id={questionkey}
                  className={"uk-width-1-1 "}
                  value={this.state.value}
                  onSelect={this.handleSelect}
                  onChange={this.handleChange}
                />
              </div>
            )}
          </div>
          <div className="uk-width-1-6">
            <a
              onClick={event => submit(input)}
              className={
                "uk-width-1-1 uk-button uk-padding-remove " +
                (nonEmpty && hasChanged ? "uk-button-success" : "")
              }
            >
              {pending && <i className="uk-icon-cog uk-icon-spin" />}
              {!pending && <i className="uk-icon uk-icon-send" />}
            </a>
          </div>
        </div>
        {error && !hasChanged && <Alert message={error} type="error" key="err" />}
        {author_error && this.props.isAuthor && <Alert message={author_error} type="error" key="author_error" />}
        {warning && (!hasChanged || notanswerbox) && <Alert message={warning} type="warning" key="warning" />}
        {hint && <Alert message={hint} type="primary" key="renderhint" />}
        <div className="uk-flex">
          <span className={"uk-width-1-1 "}>{graderResponse}</span>
        </div>
      </div>
    );
  }
}

//Register the question component with the system
registerQuestionType("pythonic", QuestionPythonic);
