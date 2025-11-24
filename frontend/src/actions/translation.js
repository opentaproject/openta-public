// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

function updateLanguage(language) {
  return {
    type: 'UPDATE_LANGUAGE',
    language: language
  };
}

export { updateLanguage };
