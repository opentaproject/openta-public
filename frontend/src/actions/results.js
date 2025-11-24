// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

function updateCustomResults(data) {
  return {
    type: 'UPDATE_CUSTOM_RESULTS',
    data: data
  };
}

export { updateCustomResults };
