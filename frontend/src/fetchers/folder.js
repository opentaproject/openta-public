import { jsonfetch, sendFrontendLog } from '../fetch_backend.js';

function fetchAddFolder(path, name, course_pk) {
  console.dir(course_pk);
  return (dispatch) => {
    var payload = {
      path: '/' + path.join('/'),
      course_pk: course_pk,
      name: name
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/folder/add/', fetchconfig)
      .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        }
      })
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'fetchAddFolder failed', { path, name, course_pk, error: String(err) });
      });
  };
}

function fetchFolderHandle(path, coursePk, action) {
  return (dispatch) => {
    var payload = {
      path: path,
      coursePk: coursePk,
      action
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/folder/handle', fetchconfig).catch((err) => {
      console.dir(err);
      sendFrontendLog('error', 'fetchFolderHandle failed', { path, coursePk, action, error: String(err) });
    });
  };
}

function fetchFolderMove(path) {
  return (dispatch) => {
    var payload = {
      new_folder: path
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/folder/move/', fetchconfig)
      .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        } else {
          return json;
        }
      })
      .catch((err) => {
        console.warn('Failed to move folder', path, err);
        sendFrontendLog('error', 'fetchFolderMove failed', { path, error: String(err) });
      });
  };
}

function fetchFolderRename(path, newName, course_pk) {
  return (dispatch) => {
    var payload = {
      old_folder: path.join('/'),
      new_folder: newName,
      course_pk: course_pk
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/folder/rename/', fetchconfig)
      .then((res) => res.json())

      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        } else {
          return json;
        }
      })
      .catch((err) => {
        console.warn('Failed to rename folder', { path, newName }, err);
        sendFrontendLog('error', 'fetchFolderRename failed', { path, newName, course_pk, error: String(err) });
      });
  };
}

function fetchDeleteFolder(folderPath) {
  return (dispatch) => {
    var fetchconfig = {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    };
    return jsonfetch('/folder/' + folderPath + '/delete', fetchconfig)
      .then((res) => res.json())
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'fetchDeleteFolder failed', { folderPath, error: String(err) });
      });
  };
}

export { fetchAddFolder, fetchDeleteFolder, fetchFolderMove, fetchFolderRename, fetchFolderHandle };
