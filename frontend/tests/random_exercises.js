module.exports = {
  'Login': function(browser) {
    browser
      .url('http://localhost:8000')
      .waitForElementVisible('body', 1000)
      .setValue('input[id=id_username]', 'student')
      .setValue('input[id=id_password]', 'learning')
      .waitForElementVisible('input[type=submit]', 1000)
      .click('input[type=submit]')
      .pause(1000)
      .assert.containsText('#login', 'student')
  },

  'Open random exercise': function(browser) {
    var page = browser.page.main();
    for(var i = 0; i < 10; i++) {
      page.selectRandomExercise();
      page.backToCourse();
    }
    browser.end()
  },

  'Try answer': '' + function(browser) {
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

}
