exports.config = {
  //hot: true,

  npm: { styles: { codemirror: ['lib/codemirror.css', 'theme/paraiso-light.css'] } },
  files: {
    //javascripts: { joinTo: {
    //  //'app.js': ['app/**/*', '../questiontypes/**/*'],
    //  'app.js': ['app/**/*', '../questiontypes/**/*'],
    //  'libraries.js': /^(?!app\/)/
    //} },
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
        //["module-resolver", {
        //"root": ["../questiontypes/", "./"],
      //}]
      ]
    },
    afterBrunch: [
	'mkdir ../django/backend/static/',
      'cp -r public/* ../django/backend/static/'
    ]
  }
};
