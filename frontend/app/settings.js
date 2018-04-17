/* Link settings.js to this to make SUBPATH authomatic  */
/*
 * If the installation is available at a subpath. (Also needs to be set in django settings.py)
 * Example: If site is available at http://domain.com/subpath
 * (Note preceding slash below!)
 * var SUBPATH = "/subpath"
 */
import {getcookie} from 'cookies.js';
const COOKIE_SUBPATH = getcookie('subpath')[0]
const SUBPATH =  (COOKIE_SUBPATH !== '""' && COOKIE_SUBPATH !== '') ?  '/' + getcookie('subpath')[0]  : ''
export {SUBPATH};