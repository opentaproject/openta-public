module.exports = {
  'Login': function(browser) {
    browser
      .url('http://localhost:8000')
      .waitForElementVisible('body', 1000)
      .setValue('input[id=id_username]', 'teacher')
      .setValue('input[id=id_password]', 'learning')
      .waitForElementVisible('input[type=submit]', 1000)
      .click('input[type=submit]')
      .pause(1000)
      .assert.containsText('#login', 'teacher')
  },

  'Open exercise': function(browser) {
    browser
      .waitForElementVisible('li#d8128074-9fb7-4aeb-b90c-61cd2d21dc7a', 1000)
      .click('li#d8128074-9fb7-4aeb-b90c-61cd2d21dc7a')
      .waitForElementVisible('h1.uk-article-title', 1000)
      .verify.containsText('h1.uk-article-title', '2/126')
  },

  'Try answer': function(browser) {
      browser
      .waitForElementVisible('input[type=text]', 1000)
      .clearValue('input[type=text]')
      .setValue('input[type=text]',['R', browser.Keys.ENTER])
      .waitForElementVisible('div.uk-alert.uk-alert-warning',1000)
      .assert.containsText('div.uk-alert-warning', 'incorrect')
      .clearValue('input[type=text]')
      .setValue('input[type=text]',['v^2/g/R^2*((a-b)^2+c^2)^(3/2)/c', browser.Keys.ENTER])
      .waitForElementVisible('div.uk-alert.uk-alert-success',1000)
      .assert.containsText('div.uk-alert-success', 'is correct')
  },

  'Back to course view': function(browser) {
    browser
    .click('ul.exercise-menu > li.uk-nav-header > a')
    .waitForElementPresent('ul.uk-thumbnav', 1000)
    .assert.containsText('#main', 'Dynamics v1 a')
    .end()
  }
}
