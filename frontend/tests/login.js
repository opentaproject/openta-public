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
      .pause(1000)
      .assert.containsText('h1.uk-article-title', '2/126')
      .end()
  }
}
