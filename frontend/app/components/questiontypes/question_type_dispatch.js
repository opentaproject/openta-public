const questionDispatch = {
  //'compareNumeric': QuestionCompareNumeric,
  //'none': 'div'
};

function registerQuestionType(type, component) {
  questionDispatch[type] = component
}

export { questionDispatch, registerQuestionType };
