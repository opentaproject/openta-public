# OpenTA documentation

The documentation uses [Sphinx](http://www.sphinx-doc.org/) (with recommonmark for [Markdown](https://en.wikipedia.org/wiki/Markdown) support) which can be installed within a python environment (or globally) with
```
pip install Sphinx recommonmark
```

To update the repository documentation in ```/docs```
```
make html
```

For live editing the documentation install ```sphinx-autobuild``` with
```
pip install sphinx-autobuild
```

and run

```
sphinx-autobuild . _build_html
```

This will set up an local webserver at http://127.0.0.1:8000 that recompiles on file changes.

Maybe you are using Vim and also want to specify a port:
```
sphinx-autobuild -p 8005 --ignore "*.swp" --ignore "*.swx" --ignore "*~" . _build_html
```
