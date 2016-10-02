var commands = {
  selectRandomExercise: function() {
    var api = this.api;
    api.elements('css selector', 'li.course-exercise-item', function(result) {
      console.dir(result);
      var els = result.value;
      var num = els.length;
      var i = Math.floor(Math.random() * num + 1);
      api.elementIdClick(els[i].ELEMENT);
    });
    return this.waitForElementVisible('h1.uk-article-title', 1000)

  },
  backToCourse: function() {
    this
    .click('ul.exercise-menu > li.uk-nav-header > a')
    .waitForElementPresent('li.course-exercise-item', 1000)
  }
}

module.exports = {
  commands: [commands],
  elements: {
    courseExercises: {
      selector: 'li.course-exercise-item'
    }
  }
};

