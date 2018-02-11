exports.config = {
 watcher: {
     awaitWriteFinish: true,
     usePolling: true
   },
  npm: { styles: { codemirror: ['lib/codemirror.css', 'theme/paraiso-light.css', 'addon/fold/foldgutter.css', '/addon/hint/show-hint.css'] } },
  files: {
    javascripts: { joinTo: 'app.js' },
    stylesheets: { joinTo: 'app.css' }
  },
  paths: {
    watched: ['app', '../questiontypes']
  },

  plugins: {
    babel: {
      presets: ['es2015', 'react'],
      plugins: [
        "transform-class-properties",
        "transform-object-rest-spread",
      ]
    },
    afterBrunch: [
	    'mkdir -p ../django/backend/static/',
      'cp -r public/* ../django/backend/static/'
    ]
  }
};
