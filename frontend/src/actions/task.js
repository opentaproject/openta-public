function updateTask(taskId, data) {
  return {
    type: 'UPDATE_TASK',
    task: taskId,
    data: data
  };
}

export { updateTask };
