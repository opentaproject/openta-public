// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { useRef, createRef, Component } from "react";
import immutable from "immutable";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import ReactDOM from "react-dom";

import { whiteTheme } from "./white-theme";
import { reUploadImage } from "../fetchers.js";

const nextUnstableKey = () => unstableKey++;
var unstableKey = 99552;

import ImageEditor from "./ImageEditor";
import LoadFromUrl from "./LoadFromUrl";

export class BaseMyImageEditor extends Component {
  constructor() {
    super();
    this.state = {
      count: 0,
    };
  }
  static propTypes = {
    src: PropTypes.string,
    exerciseKey: PropTypes.string,
    onNext: PropTypes.func,
    onPrev: PropTypes.func,
    imgLabel: PropTypes.string,
  };

  handleUpload = (dispatch, exerciseKey, file, src, action) => {
    event.target.value = "";
    // see https://stackoverflow.com/questions/12030686/html-input-file-selection-event-not-firing-upon-selecting-the-same-file
    dispatch(reUploadImage(exerciseKey, file, src, action)).then((res) => {
      if ("error" in res) {
        UIkit.notify(res.error, { timeout: 10000, status: "danger" });
      } else if ("success" in res) {
        UIkit.notify(res.success, { timeout: 10000, status: "success" });
      } else if ("warning" in res) {
        UIkit.notify(res.warning, { timeout: 10000, status: "warning" });
      }
    });
    if (action == 'reset' ){
        setTimeout( () => this.setState({ count: this.state.count + 1 }), 1000 ) ; // Force a rerender on reset
	}
  };

  // https://stackoverflow.com/questions/55718473/writing-tui-image-editor-canvass-to-server
  // https://codesandbox.io/s/7ytvs?file=/src/ImageEditor.js

  render() {
    var editorRef = createRef();
    var path = this.props.src;
    var exerciseKey = this.props.exerciseKey;
    var pathname = path.toString();
    return (
      <div className="editor-container">
        <div className="editor-container" key={pathname + nextUnstableKey()}>
          <ImageEditor
            onNext={this.props.onNext}
            onPrev={this.props.onPrev}
            imgLabel={this.props.imgLabel}
            handleUpload={this.handleUpload}
            ref={editorRef}
            exerciseKey={exerciseKey}
            src={pathname}
            includeUI={{
              loadImage: {
                path: path,
                name: "SampleImage",
              },
              theme: whiteTheme,
              menu: [
                "crop",
                "flip",
                "rotate",
                "draw",
                "shape",
                "icon",
                "text",
                "filter",
              ],
              uiSize: {
                width: "100%",
                height: "700px",
              },
              menuBarPosition: "bottom",
            }}
            cssMaxHeight={800}
            cssMaxWidth={1200}
            selectionStyle={{
              cornerSize: 20,
              rotatingPointOffset: 70,
            }}
            usageStatistics={false}
          />
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  var key = state.get("activeExercise");
  var activeExerciseState = state.getIn(
    ["exerciseState", state.get("activeExercise")],
    immutable.Map({})
  );
  return {
    exerciseKey: key,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event, exerciseKey, editorRef, fileFromEditorRef, src, action) =>
      this.handleUpload(
        dispatch,
        event,
        exerciseKey,
        editorRef,
        fileFromEditorRef,
        src,
        action
      ),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseMyImageEditor);
