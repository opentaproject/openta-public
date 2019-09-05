/* Link settings.js to this to make SUBPATH authomatic  */
/*
 * If the installation is available at a subpath. (Also needs to be set in django settings.py)
 * Example: If site is available at http://domain.com/subpath
 * (Note preceding slash below!)
 * var SUBPATH = "/subpath"
 */
const SUBPATH = globalInit.subpath;
export {SUBPATH};