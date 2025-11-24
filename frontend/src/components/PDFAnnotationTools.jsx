// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

/*
Copyright 2020 Adobe
All Rights Reserved.

NOTICE: Adobe permits you to use, modify, and distribute this file in
accordance with the terms of the Adobe license agreement accompanying
it. If you have received this file from a source other than Adobe,
then your use, modification, or distribution of it requires the prior
written permission of Adobe.
*/
import { env_source , adobe_id } from '../settings';
import React, { Component } from "react";
import { useDispatch } from "react-redux";
import PropTypes from 'prop-types';
import { reUploadImage } from "../fetchers.js";
import { uploadImage } from "../fetchers.js";

import { connect } from 'react-redux';
import { uploadAsset } from '../fetchers/assets.js';





class ViewSDKClient {
    constructor() {
        this.readyPromise = new Promise((resolve) => {
            if (window.AdobeDC) {
                resolve();
            } else {
                /* Wait for Adobe Acrobat Services PDF Embed API to be ready */
                document.addEventListener("adobe_dc_view_sdk.ready", () => {
                    resolve();
                },{passive: true} );
            }
        });
        this.adobeDCView = undefined;
    }

    ready() {
        return this.readyPromise;
    }

    previewFile(divId, viewerConfig) {
        const config = {
            /* Pass your registered client id */
            clientId: adobe_id,
        };
        if (divId) { /* Optional only for Light Box embed mode */
            /* Pass the div id in which PDF should be rendered */
            config.divId = divId;
        }
        /* Initialize the AdobeDC View object */
        this.adobeDCView = new window.AdobeDC.View(config);
	var url = String( viewerConfig.url );
	var exerciseKey = viewerConfig.exerciseKey

        /* Invoke the file preview API on Adobe DC View object */
	var content = {
                /* Location of file where it is hosted */
                location: {
                    url: url,
                },
            };
	var metaData = { /* file name */
                fileName: url,
		src: url,
		exerciseKey:  exerciseKey,
                id: adobe_id,
            }

        const previewFilePromise = this.adobeDCView.previewFile({
            /* Pass information on how to access the file */
            content: content,
            /* Pass meta data of file */
            metaData: metaData,
        }, viewerConfig);

        return previewFilePromise;
    }  //http://canary.localhost:8000/imageanswer/2

    previewFileUsingFilePromise(divId, filePromise, fileName) {
        /* Initialize the AdobeDC View object */
        this.adobeDCView = new window.AdobeDC.View({
            /* Pass your registered client id */
            clientId: adobe_id,
            /* Pass the div id in which PDF should be rendered */
            divId,
        });

        /* Invoke the file preview API on Adobe DC View object */
        this.adobeDCView.previewFile({
            /* Pass information on how to access the file */
            content: {
                /* pass file promise which resolve to arrayBuffer */
                promise: filePromise,
            },
            /* Pass meta data of file */
            metaData: {
                /* file name */
                fileName: fileName
            },
	   options: {'a': 'b'},
        }, {"c": "d" });
    }

    registerSaveApiHandler(reUploadImage) {
        /* Define Save API Handler */
        const saveApiHandler = (metaData, content, options) => {
            return new Promise(resolve => {
                /* Dummy implementation of Save API, replace with your business logic */
                setTimeout(() => {
                    const response = {
                        code: window.AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
                        data: {
                            metaData: Object.assign(metaData, {updatedAt: new Date().getTime()})
                        },
                    };
                    resolve(response);
                }, 2000);
            });
        };

	// https://community.adobe.com/t5/acrobat-services-api-discussions/is-there-any-way-to-save-edited-pdf-in-server-in-pdf-embed-api/td-p/11767431
        this.adobeDCView.registerCallback(
            window.AdobeDC.View.Enum.CallbackType.SAVE_API,
	    function(metaData, content, options) {
      		/* Add your custom save implementation here...and based on that resolve or reject response in given format */
		var uint8Array = new Uint8Array(content);
        	var blob = new Blob([uint8Array], { type: 'application/pdf' });
		const file = new File([blob], "edited-image.pdf", {
      			type: "application/pdf",
      			lastModified: new Date(),
    			});
		let action = 'save'
		let src = metaData.src
		let exerciseKey = metaData.exerciseKey
		reUploadImage(exerciseKey, file,src,action);
      		return new Promise((resolve, reject) => {
         		resolve({
            			code: AdobeDC.View.Enum.ApiResponseCode.SUCCESS,
            			data: {
               				/* Updated file metadata after successful save operation */
               			metaData: {},
            			}
         		});
      		   });
   		},
  	    {}

          );
        }

    registerEventsHandler() {
        /* Register the callback to receive the events */
        this.adobeDCView.registerCallback(
            /* Type of call back */
            window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
            /* call back function */
            event => {
                console.log(event);
            },
            /* options to control the callback execution */
            {
                /* Enable PDF analytics events on user interaction. */
                enablePDFAnalytics: true,
            } 
        );
    }
}


class PDFAnnotationTools extends Component {

    constructor(props) {
    super(props);
    this.myRef = React.createRef();
    this.state =  { exerciseKey: this.props.exerciseKey , error: false , imagekey: this.props.imagekey };
  }
 

 static propTypes = {
    src: PropTypes.string,
    close: PropTypes.func,
    imagekey: PropTypes.number,
  };






    componentDidMount() {
        const viewSDKClient = new ViewSDKClient();
	var urlstring = String( this.props.src)
	var exerciseKey = this.props.exerciseKey
        viewSDKClient.ready().then(() => {
            /* Invoke file preview */
            viewSDKClient.previewFile("pdf-div",  {
                /* Control the viewer customization. */
		url: urlstring,
		exerciseKey: exerciseKey,
                showAnnotationTools: true,
                enableFormFilling: true
            });
            /* Register Save API handler */
            viewSDKClient.registerSaveApiHandler(this.props.reUploadImage);
        });
    }

    render() {
        return (
            <div id="pdf-div" className="full-window-div"/>
        );
    }
}

const mapDispatchToProps = (dispatch) => {
  return {
    //doUpload: (exerciseKey, f) => dispatch(uploadAsset(exerciseKey, f)).catch((err) => console.log(err)),
    //doUploadImage: (exerciseKey, f) => dispatch(uploadImage(exerciseKey, f)).catch((err) => console.log(err)),
    reUploadImage: (exerciseKey, file, src, action)  => dispatch( reUploadImage(exerciseKey, file, src, action)).catch((err) => console.log(err)),
  };
};


export default connect(null, mapDispatchToProps)(PDFAnnotationTools);
