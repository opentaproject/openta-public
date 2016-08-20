exports.config = {
  hot: true,

  npm: { styles: { codemirror: ['lib/codemirror.css', 'theme/monokai.css'] } },
  files: {
    javascripts: { joinTo: 'app.js' },
    stylesheets: { joinTo: 'app.css' }
  },

  plugins: {
    babel: { 
      presets: ['es2015', 'react'],
      plugins: ["transform-class-properties"]
    },
    afterBrunch: [
	'mkdir ../django/backend/static/',
      'cp -r public/* ../django/backend/static/'
    ]
  }
};
