export default (state = { exercises: ['test'] }, action) => {
  switch (action.type) {
    case 'EXERCISECLICK':
      return state;
    case 'UPDATE_EXERCISES':
      return Object.assign({}, state, {exercises: action.exercises});
    default:
      return state
  }
}
