import React, { useState, useEffect, useRef, forwardRef } from "react";
import TuiImageEditor from "tui-image-editor";
import { useDispatch } from "react-redux";
import { reUploadImage } from "../fetchers.js";

//import "tui-image-editor/dist/tui-image-editor.css";
//import "tui-color-picker/dist/tui-color-picker.css";

const getNumber = (value) => Number(value.replace("px", ""));

const resizeElement = (element, percentage, props = [], values = []) => {
  props.forEach((key, idx) => {
    element.style[key] = values[idx] * percentage + "px";
  });
};

const ImageEditor = forwardRef((props, ref) => {
  const [zoom, setZoom] = useState(1);
  const maxZoom = 2;
  const minZoom = 0.5;
  const [height, setHeight] = useState(0);
  const [width, setWidth] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const instance = useRef(null);
  const rootEl = useRef(null);
  const dispatch = useDispatch();

  const dataURItoBlob = (dataURI) => {
    var byteString = atob(dataURI.split(",")[1]);
    var mimeString = dataURI.split(",")[0].split(":")[1].split(";")[0];
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);
    for (var i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
  };

  const fileFromInstance = (instance) => {
    const editorInstance = instance.current;
    const data = editorInstance.toDataURL();
    var blob = dataURItoBlob(data);
    const file = new File([blob], "edited-image.png", {
      type: "image/png",
      lastModified: new Date(),
    });
    return file;
  };

  useEffect(() => {
    instance.current = new TuiImageEditor(rootEl.current, {
      ...props,
    });
    instance.current.on("objectActivated", function (evt, a, b) {
      setLoaded(false);
      setZoom(1);
    });
    return () => {
      instance.current.destroy();
      instance.current = null;
    };
  }, [instance, props]);

  const reUpload = (action) => {
    var file = fileFromInstance(instance);
    props.handleUpload(dispatch, props.exerciseKey, file, props.src, action);
  };
  const zoomChange = (type) => {
    let updated = zoom;

    if (type === "in") {
      updated = updated + 0.25;
    } else {
      updated = updated - 0.25;
    }
    setZoom(updated);
    let maxHeight = height;
    let maxWidth = width;
    if (!loaded) {
      const canvas = document.querySelector("canvas");
      maxHeight = getNumber(canvas.style.maxHeight);
      maxWidth = getNumber(canvas.style.maxWidth);
      setHeight(maxHeight);
      setWidth(maxWidth);
      setLoaded(true);
    }
    resizeElement(
      document.querySelector(".tui-image-editor"),
      updated,
      ["height", "width"],
      [maxHeight, maxWidth]
    );
    resizeElement(
      document.querySelector(".tui-image-editor-canvas-container"),
      updated,
      ["maxHeight", "maxWidth"],
      [maxHeight, maxWidth]
    );
    document.querySelectorAll("canvas").forEach((element) => {
      resizeElement(
        element,
        updated,
        ["maxHeight", "maxWidth"],
        [maxHeight, maxWidth]
      );
    });
  };

  return (
    <div className="PR">
      <span className="zoom uk-width-1-1">
        <div className="uk-button-group uk-margin-small">
          {props.imgLabel && (
            <div>
              <button
                onClick={() => 
                  props.onPrev()
                }
                className="uk-button-primary uk-button-large uk-margin-small"
              >
                Previous
              </button>
              <button
                className="uk-button-success uk-button-large uk-margin-small"
                disabled
              >
                {props.imgLabel}
              </button>
              <button
                onClick={() => 
                  props.onNext()
                }
                className="uk-button-primary uk-button-large uk-margin-small"
              >
                Next
              </button>
            </div>
          )}
          <button
            onClick={() =>  reUpload("save")} 
            className="uk-button-primary uk-button-large uk-margin-small"
          >
            Save edited
          </button>
          <button
            className="uk-button-large uk-margin-small"
            onClick={() => zoomChange("in")}
          >
            Zoom in
          </button>
          <button
            className="uk-button-success uk-button-large uk-margin-small"
            disabled
          >
            {zoom * 100}%
          </button>
          <button
            className="uk-button-large uk-margin-small"
            onClick={() => zoomChange("out")}
          >
            Zoom out
          </button>
          <button
            onClick={() => reUpload("reset")}
            className="uk-button-primary uk-button-large uk-margin-small"
          >
            Reset original
          </button>
        </div>
      </span>
      <div ref={rootEl} />
    </div>
  );
});

export default ImageEditor;
