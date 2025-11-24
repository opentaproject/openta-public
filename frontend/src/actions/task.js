// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

function updateTask(taskId, data) {
  return {
    type: 'UPDATE_TASK',
    task: taskId,
    data: data
  };
}

export { updateTask };
