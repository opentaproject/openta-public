// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import SafeImg from './SafeImg.jsx';
import SafeTextarea from './SafeTextarea';
import { SUBPATH } from '../settings.js';
import { updatePendingStateIn, uploadAsset, deleteAsset, fetchAssets, runAsset  } from '../fetchers.js';

import { handleReset } from './LoginInfo.jsx';

// https://codepen.io/iamrewt/pen/WYbPWN
//
function copyStyles(sourceDoc, targetDoc) {
  Array.from(sourceDoc.styleSheets).forEach((styleSheet) => {
    if (styleSheet.href) {
      // true for stylesheets loaded from a URL
      const newLinkEl = targetDoc.createElement('link');

      newLinkEl.rel = 'stylesheet';
      newLinkEl.href = styleSheet.href;
      targetDoc.head.appendChild(newLinkEl);
    }
  });
}


const long_interval =  2147483647 ; // 2^31 - 1
const short_interval = 1000;

class MyWindowPortal extends React.PureComponent {
  constructor(props) {
    super(props);
    this.containerEl = null;
    this.externalWindow = null;
  }

  componentDidMount() {
    // Create a new window, a div, and append it to the window
    // The div **MUST** be created by the window it is to be
    // appended to or it will fail in Edge with a "Permission Denied"
    // or similar error.
    // See: https://github.com/rmariuzzo/react-new-window/issues/12#issuecomment-386992550
    this.externalWindow = window.open('', '', 'width=1200,height=400,left=100,top=100');
    this.containerEl = this.externalWindow.document.createElement('div');
    this.externalWindow.document.body.appendChild(this.containerEl);

    this.externalWindow.document.title = 'editor';
    copyStyles(document, this.externalWindow.document);

    // update the state in the parent component if the user closes the
    // new window
    this.externalWindow.addEventListener('beforeunload', () => {
      this.props.closeWindowPortal();
    });
  }

  componentWillUnmount() {
    // This will fire when this.state.showWindowPortal in the parent component becomes false
    // So we tidy up by just closing the window
    this.externalWindow.close();
  }

  render() {
    // The first render occurs before componentDidMount (where we open
    // the new window), so our container may be null, in this case
    // render nothing.
    if (!this.containerEl) {
      return null;
    }

    // Append props.children to the container <div> in the new window
    return ReactDOM.createPortal(this.props.children, this.containerEl);
  }
}

class BaseAssets extends Component {
  constructor() {
    super();
    this.state = {
      preview: false,
      counter: 0,
      nrenders: 0 ,
      showWindowPortal: false,
      interval: long_interval,
      myinterval:   null,
    };
    this.toggleWindowPortal = this.toggleWindowPortal.bind(this);
    this.closeWindowPortal = this.closeWindowPortal.bind(this);
  }

  componentDidMount() {
    window.addEventListener('beforeunload', () => {
      this.closeWindowPortal();
    //window.setInterval(() => {
    //  this.setState((state) => ({
    //    counter: state.counter + 1
    //  }));
    //}, this.state.interval);
    
    });

  }

  toggleWindowPortal(filename) {
    this.setState((state) => ({
      ...state,
      showWindowPortal: !state.showWindowPortal,
      filename: filename
    }));
  }

  closeWindowPortal() {
    this.setState({ showWindowPortal: false, filename: null });
  }

  handlePreviewChange = (e) => {
    this.setState({ preview: e.target.checked });
  };

  renderAsset = (asset, locked) => {
    var is_editable = this.props.editables.indexOf(asset.get('filename').split('.').pop()) > -1;
    var is_runnable = this.props.runnables.indexOf(asset.get('filename').split('.').pop()) > -1;
    if ( asset.get('filename') == 'index.html' && ! this.props.author ){
	    return ''
    }
    return (
      <tr key={'abcde' + asset.get('filename')}>
        <td>

          {this.props.pendingState.getIn(['asset', 'delete', asset.get('filename')]) && <Spinner size="" />}
          {!locked && !this.props.pendingState.getIn(['asset', 'delete', asset.get('filename')]) && (
            <a
              onClick={(e) =>
                UIkit.modal.confirm('Delete asset ' + asset.get('filename') + '?', () =>
                  this.props.handleDeleteAsset(this.props.activeExercise, asset.get('filename'))
                )
              }

              className="uk-icon-hover uk-icon-trash"
            ></a>



          )}



        </td>

        <td>
          {is_editable && (
            <div>
              <div onClick={() => this.toggleWindowPortal(asset.get('filename'))}>
                {this.state.showWindowPortal ? (
                  ''
                ) : (
                  <i className="uk-icon uk-icon-edit uk-margin-small-left uk-margin-small-right" />
                )}
              </div>
            </div>
          )}
	   </td><td>
      {is_runnable && (
            <div>
              <div onClick={(e) =>
                UIkit.modal.confirm('Run asset ' + asset.get('filename') + '?', () =>
                  this.props.handleRunAsset(this.props.activeExercise, asset.get('filename'))
                ) }
	      >
                  <i className="uk-icon uk-icon-sitemap uk-margin-small-left uk-margin-small-right"  />
              </div>
            </div>
          )}


        </td>
        <td>
          <a
            href={SUBPATH + '/exercise/' + this.props.activeExercise + this.props.assetViewer + asset.get('filename')}
            target="_blank"
	    referrerPolicy="origin-when-cross-origin"
          >
            {asset.get('filename')}
          </a>
        </td>
        {this.state.preview && (
          <td>
            <div className="uk-thumbnail uk-thumbnail-mini" style={{ maxWidth: '80px' }}>
              <SafeImg
                src={
                  SUBPATH + '/exercise/' + this.props.activeExercise + this.props.assetViewer + asset.get('filename')
                }
              />
            </div>
          </td>
        )}

        <td>
          {' '}
          <span className="uk-text uk-text-small uk-text-primary"> {asset.get('date')} </span>{' '}
        </td>
        <td>
          {' '}
          <span className="uk-text uk-text-small uk-text-primary uk-align-right">
            {' '}
            {asset.get('size') + ' bytes'}{' '}
          </span>{' '}
        </td>
      </tr>
    );
  };

  renderProgress = () => (
    <span className="uk-button">
      <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{ width: '100px' }}>
        <div className="uk-progress-bar" style={{ width: this.props.uploadProgress * 100 + '%' }}></div>
      </div>
    </span>
  );

  renderDownload = () => {
    return (
      <span className="uk-margin-left">
        <div>
          <a className={'uk-button'} href={SUBPATH + '/exercise/' + this.props.activeExercise + '/download_assets'}>
            <i className="uk-icon-download" title="download" />{' '}
          </a>
        </div>
      </span>
    );
  };

  renderUpload = () => {
    return (
      <span className="uk-margin-left">



        <div className="uk-form-file">
          <a type="file" className={'uk-button'}>
            <i className="uk-icon-upload" title="Choose a file to upload" />
          </a>
          <input type="file" onChange={(e) => this.props.onUpload(e, this.props.activeExercise, this.props.author)} />
        </div>

        <div className="uk-form-file">
          <a type="file" className={'uk-button'} title="Choose from photos">
            <i className="uk-icon-image" />
          </a>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => this.props.onUpload(e, this.props.activeExercise, this.props.author)}
          />
        </div>

	<div className="uk-form-file">
            <a type="file" className={'uk-button'} capture="camera"> <i className="uk-icon-camera"></i>
            <input type="file" accept="image/*" onChange={(e) => this.props.onUpload(e, this.props.activeExercise , this.props.author)} capture />
	    </a>
          </div>


      </span>
    );
  };

  render() {
    /*
     * List of files
     * Ability to delete
     * Ability to preview
     * Upload
     */
    //console.log("RENDER_ASSETS", this.state.interval , this.state.nrenders)
    this.state.nrenders = this.state.nrenders + 1;
    // console.log("SHOW WINDOW PORTAL ", this.state.nrenders, "SHOW PORTAL " , this.state.showWindowPortal)
    if ( this.state.showWindowPortal && this.state.interval != short_interval ){ 
	//console.log("START THHE TIMER")
	this.state.interval = short_interval;
	this.state.myinterval = window.setInterval(() => {
      		this.setState((state) => ({
        	counter: state.counter + 1
      		}));
    	}, short_interval );

	}
    if ( ! this.state.showWindowPortal && this.state.interval == short_interval ) {
	    //console.log("STOP THE TIMER")
	    clearInterval( this.state.myinterval)
	    this.state.interval = long_interval
	    this.state.myinterval = window.setInterval(() => {
      		this.setState((state) => ({
        	counter: state.counter + 1
      		}));
    	   }, long_interval ,);

    }
	    
    const sortedAssets = this.props.assets.sort((a, b) => a.get('filename') > b.get('filename'));
    var locked = this.props.locked && !this.props.author;
    const renderedAssets = sortedAssets.map((asset) => this.renderAsset(asset, locked));

    return (
      <div key="abcdegkk.">
        {this.state.showWindowPortal && (
          <MyWindowPortal closeWindowPortal={this.closeWindowPortal}>
            <SafeTextarea
              close={this.closeWindowPortal}
              src={'/exercise/' + this.props.activeExercise + this.props.assetViewer + this.state.filename}
            />
          </MyWindowPortal>
        )}

        <div>
          <button className="uk-button" data-uk-toggle="{target: '.toggle'}">
            {' '}
            Assets{' '}
          </button>
          <div className="toggle uk-hidden">
            <div className="uk-flex uk-width-1-1 uk-flex-space-between">
              <div>
	    <span>
                <form className="uk-form">
                  <button>
                    <input type="checkbox" value={this.state.preview} onChange={this.handlePreviewChange} /> Preview
                  </button>

	    	  <button type="button" onClick={(e) =>
                		UIkit.modal.confirm('Cleanup assets ?', () =>
                  		this.props.handleHandleAsset(this.props.activeExercise, "cleanup_assets")
                		) }> Cleanup  </button>
                </form>
	    </span>


              </div>
              {!locked && this.renderUpload()}
              {this.renderDownload()}
            </div>
            {this.props.pendingUpload && this.renderProgress()}
            <table className="uk-table uk-table-condensed">
              <tbody>{renderedAssets}</tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }
}

const handleUpload = (event, exerciseKey, author) => (dispatch) => {
  if (event.target.value !== '') {
    var file = event.target.files[0];
    var extension = file.name.split('.').pop();
    if (author && extension.match(/(gz|zip)/)) {
      dispatch(uploadAsset(exerciseKey, file))
        .then(() => dispatch(handleReset(exerciseKey))) // Only author is allowed to reset after upload since others dont change xml
        .catch((err) => console.log(err));
    } else {
      dispatch(uploadAsset(exerciseKey, file)).catch((err) => console.log(err));
    }
    event.target.value = '';
  }
};

const handleDeleteAsset = (exerciseKey, asset) => (dispatch) => {
  dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], true));
  dispatch(deleteAsset(exerciseKey, asset))
    .then(() => dispatch(fetchAssets()))
    .then(() => dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], false)))
    .catch((err) => {
      console.dir(err);
      dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], true));
    });
};


const handleHandleAsset = (exerciseKey, asset) => (dispatch) => {
  dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], true));
  dispatch(runAsset(exerciseKey, asset))
    .then(() => dispatch(fetchAssets()))
    .then(() => dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], false)))
    .catch((err) => {
      console.dir(err);
      dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], true));
    });
};




const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event, exerciseKey, author) => dispatch(handleUpload(event, exerciseKey, author)),
    handleDeleteAsset: (exerciseKey, asset) => dispatch(handleDeleteAsset(exerciseKey, asset)),
    handleHandleAsset: (exerciseKey, key ) => dispatch(handleHandleAsset(exerciseKey, key )),
    handleRunAsset: (exerciseKey, asset ) => dispatch(handleHandleAsset(exerciseKey, asset)),
  };
};

const mapStateToProps = (state) => {
  var activeExercise = state.get('activeExercise');
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  var pendingState = state.getIn(['pendingState', 'exercise', state.get('activeExercise')], immutable.Map({}));
  var assetViewer = '/studentasset/';
  var author = state.getIn(['login', 'groups'], immutable.List([])).includes('Author');
  var assetViewer = author ? '/asset/' : '/studentasset/';
  //if(state.getIn(["login", "groups"], immutable.List([])).includes("Student"))
  //  var assetViewer = '/studentasset/';
  return {
    activeExercise: activeExercise,
    assets: activeExerciseState.getIn(['assets','files'], immutable.List([])),
    runnables: activeExerciseState.getIn(['assets','runnables'], immutable.List([])), 
    editables: activeExerciseState.getIn(['assets','editables'], immutable.List([])), 
    pendingState: pendingState,
    pendingUpload: pendingState.getIn(['assetUploadPending']),
    uploadProgress: pendingState.getIn(['assetUploadProgress']),
    assetViewer: assetViewer,
    author: author
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseAssets);
