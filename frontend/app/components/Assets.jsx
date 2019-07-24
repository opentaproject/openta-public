import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import SafeImg from './SafeImg.jsx';
import {SUBPATH} from '../settings.js';
import _ from 'lodash';
import {
    updatePendingStateIn,
    uploadAsset,
    deleteAsset,
    fetchAssets
} from '../fetchers.js';

import {handleSave,handleReset} from "./LoginInfo.jsx"



class BaseAssets extends Component {
    constructor() {
        super();
        this.state = {
            preview: false
        }
    }

    handlePreviewChange = (e) => {
        this.setState({preview: e.target.checked});
    }

    renderAsset = (asset) => {
        return (
            <tr key={asset.get('filename')}>
            <td>
            { this.props.pendingState.getIn(['asset', 'delete', asset.get('filename')]) &&
              <Spinner size=""/>
            }
            { !this.props.pendingState.getIn(['asset', 'delete', asset.get('filename')]) &&
                <a onClick={(e) => UIkit.modal.confirm('Delete asset ' + asset.get('filename') + '?', () => this.props.handleDeleteAsset(this.props.activeExercise, asset.get('filename')))} className="uk-icon-hover uk-icon-trash">
                </a>
            }
            </td>
            <td>
                <a href={SUBPATH + "/exercise/" + this.props.activeExercise + this.props.assetViewer + asset.get('filename')} target="_blank">
                    {asset.get('filename')}
                </a>
            </td>
            {
                this.state.preview &&
                <td>
                    <div className="uk-thumbnail uk-thumbnail-mini" style={{maxWidth: '80px'}}>
                        <SafeImg src={SUBPATH + "/exercise/" + this.props.activeExercise + this.props.assetViewer + asset.get('filename')}/>
                    </div>
                </td>
            }
            </tr>
        )
    }

    renderProgress = () => (
            <span className="uk-button">
                <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{width: "100px"}}>
                    <div className="uk-progress-bar" style={{width: (this.props.uploadProgress*100) + "%"}}></div>
                </div>
            </span>
    )


    renderDownload = () => {
        return (
            <span className="uk-margin-left">
                <div>
                <a className={"uk-button"} href={SUBPATH + "/exercise/" + this.props.activeExercise  + "/download_assets" } >
                <i className="uk-icon-download" title="download"/> </a>
                </div>
            </span>
        );
    }

    renderUpload = () => {
        return (
            <span className="uk-margin-left">
                <div className="uk-form-file">
                    <a type="file" className={"uk-button"}><i className="uk-icon-camera"/>
                    </a>
                    <input type="file" accept="image/*" onChange={(e) => this.props.onUpload(e, this.props.activeExercise,this.props.author)}/>
                </div>

                <div className="uk-form-file">
                    <a type="file" className={"uk-button"}><i className="uk-icon-file-o" title="file"/>
                    </a>
                    <input type="file" onChange={(e) => this.props.onUpload(e, this.props.activeExercise,this.props.author)}/>
                </div>
            </span>
        );
    }

    render() {
        /*
           * List of files
           * Ability to delete
           * Ability to preview
           * Upload
        */
        const sortedAssets = this.props.assets.sort( (a, b) => a.get('filename') > b.get('filename'));
        const renderedAssets = sortedAssets.map( asset => this.renderAsset(asset));
        return (
            <div>

            <div>
                <button className="uk-button" data-uk-toggle="{target: '.toggle'}"> Assets </button>
                <p className='toggle uk-hidden'>
                    <div className="uk-flex uk-width-1-1 uk-flex-space-between">
                         <div><form className="uk-form"><label><input type="checkbox" value={this.state.preview} onChange={this.handlePreviewChange}/> Preview</label></form>
                         </div>
                    {this.renderUpload()}
                    {this.renderDownload()}
                    </div>
                    {this.props.pendingUpload && this.renderProgress() }
                    <table className="uk-table uk-table-condensed">
                         <tbody>
                             {renderedAssets}
                         </tbody>
                    </table>
                </p>
            </div>
        </div>
        )
    }
}

const handleUpload = (event, exerciseKey ,author ) => dispatch => {
  if (event.target.value !== "") {
    var file = event.target.files[0];
    var extension = file.name.split('.').pop()
    if(  author && extension.match(/(gz|zip)/ ) ){
        dispatch(uploadAsset(exerciseKey, file))
            .then( () => dispatch( handleReset(exerciseKey) )) // Only author is allowed to reset after upload since others dont change xml
            .catch(err => console.log(err));
        }
    else {
        dispatch(uploadAsset(exerciseKey, file))
        .catch(err => console.log(err));
        }
    event.target.value = "";
  }
};

const handleDeleteAsset = (exerciseKey, asset) => dispatch => {
    dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], true))
    dispatch(deleteAsset(exerciseKey, asset))
        .then(() => dispatch(fetchAssets()))
        .then(() => dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], false)))
        .catch(err => {
            console.dir(err)
            dispatch(updatePendingStateIn(['exercise', exerciseKey, 'asset', 'delete', asset], true))
        })
}

const mapDispatchToProps = dispatch => {
    return {
        onUpload: (event, exerciseKey,author) => dispatch(handleUpload(event, exerciseKey,author)),
        handleDeleteAsset: (exerciseKey, asset) => dispatch(handleDeleteAsset(exerciseKey, asset))
    }
}

const mapStateToProps = state => {
  var activeExercise = state.get("activeExercise");
  var activeExerciseState = state.getIn(["exerciseState", state.get("activeExercise")], immutable.Map({}));
  var pendingState = state.getIn(["pendingState", "exercise", state.get("activeExercise")], immutable.Map({}));
  var assetViewer = '/asset/';
  var author = state.getIn(['login', 'groups'], immutable.List([])).includes('Author')
  if(state.getIn(["login", "groups"], immutable.List([])).includes("Student"))
    var assetViewer = '/studentasset/';
  return {
    activeExercise: activeExercise,
    assets: activeExerciseState.get("assets", immutable.List([])),
    pendingState: pendingState,
    pendingUpload: pendingState.getIn(["assetUploadPending"]),
    uploadProgress: pendingState.getIn(["assetUploadProgress"]),
    assetViewer: assetViewer,
    author: author
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseAssets);
