// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import md5 from 'md5';

export const getkey = (txt) => {
  var altkey = txt.replace(/\s+/g, '');
  var ret = md5(altkey).substring(0, 5);
  //console.log(txt, ret )
  return ret;
};
