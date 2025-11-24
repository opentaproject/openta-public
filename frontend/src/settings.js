/* Link settings.js to this to make SUBPATH authomatic  */
/*
 * If the installation is available at a subpath. (Also needs to be set in django settings.py)
 * Example: If site is available at http://domain.com/subpath
 * (Note preceding slash below!)
 * var SUBPATH = "/subpath"
 */
import thunk from 'redux-thunk';
import { applyMiddleware, compose } from 'redux';
const SUBPATH = ''; // globalInit.subpath !== '' ? '/' + globalInit.subpath.replace(/\/$/, "") : "";
const help_url = globalInit.help_url;
const new_folder = globalInit.new_folder;
const trash_folder = globalInit.trash_folder;
const use_stars = globalInit.use_stars;
const use_chatgpt = globalInit.use_chatgpt  == 'True' ;
const use_mathpix = globalInit.use_mathpix  == 'True' ;
const sidecar_url = globalInit.sidecar_url;
const use_sidecar = globalInit.use_sidecar;
const adobe_id = globalInit.adobe_id;
const student_pk = globalInit.student_pk;
const adminurl = globalInit.adminurl;
const language_code = globalInit.language_code;
const course_pk = globalInit.course_pk
const subdomain = globalInit.subdomain;
const username = globalInit.username;
const env_source = globalInit.env_source;
const answer_delay = parseInt( globalInit.answer_delay );
const user_permissions = globalInit.user_permissions;
const use_devtools = globalInit.use_devtools == 'True';
if (use_devtools) {
  var enhancer = compose(
    applyMiddleware(thunk),
    window.__REDUX_DEVTOOLS_EXTENSION__ ? window.__REDUX_DEVTOOLS_EXTENSION__() : (f) => f
  );
} else {
  var enhancer = compose(applyMiddleware(thunk), (f) => f);
}

export {
  SUBPATH,
  help_url,
  new_folder,
  trash_folder,
  use_stars,
  use_sidecar,
  language_code,
  subdomain,
  username,
  use_devtools,
  enhancer,
  adminurl,
  student_pk,
  env_source,
  course_pk,
  adobe_id,
  answer_delay,
  user_permissions,
  sidecar_url,
  use_chatgpt,
};
