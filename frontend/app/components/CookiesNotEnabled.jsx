import React, { Component } from 'react';
import Alert from './Alert';

const Spinner = ({help_url=''} ) => {
    console.log(" SPINNER ", help_url)
    if( help_url == '' ){
    return (
    <div id="content" className="uk-width-1-1">
        <div id="main" className="uk-grid uk-margin-remove">
            <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
                <Alert>Please enable cookies (and third-party cookies) to access OpenTA.</Alert>
            </div>
        </div>
    </div>
    )
    } else {
    return (
    <div id="content" className="uk-width-1-1">
        <div id="main" className="uk-grid uk-margin-remove">
            <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
                <Alert>Please enable cookies (and third-party cookies) to access OpenTA. 
                <a href={help_url}> Click here for further help: </a> </Alert>
            </div>
        </div>
    </div>
    )


    }
}

export default Spinner