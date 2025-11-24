// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

/* Link settings.js to this to make SUBPATH authomatic  */
/*
 * If the installation is available at a subpath. (Also needs to be set in django settings.py)
 * Example: If site is available at http://domain.com/subpath
 * (Note preceding slash below!)
 * var SUBPATH = "/subpath"
 */
import { getcookie } from 'cookies.js';
const SUBPATH = getcookie('subpath')[0] !== '""' ? '/' + getcookie('subpath')[0] : '';
export { SUBPATH };
