function setExerciseHistory(exerciseKey, list) {
    return {
        type: 'SET_EXERCISE_HISTORY',
        exercise: exerciseKey,
        data: list
    };
}

export {setExerciseHistory}
