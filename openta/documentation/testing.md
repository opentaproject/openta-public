# Testing

The test suite is broken up into *backend* and *frontend* tests. The whole test suite can be run
from the command line. However, the *frontend* tests require that the Selenium ChromeDriver be
installed. See below for installation instructions.

## Selenium ChromeDriver

* You can download the driver from here: https://chromedriver.chromium.org/downloads

* MacOS installation instructions can be found here: https://www.swtestacademy.com/install-chrome-driver-on-mac/

* Linux installation instructions can be found here: https://tecadmin.net/setup-selenium-chromedriver-on-ubuntu/

## Running the test suite

### Frontend only

To run only the *frontend* tests use the following commands:

```
cd __project_root__/django
source env/bin/activate
cd __project_root__/django/backend
pytest --no-header -s --disable-warnings --reuse-db -m "end_to_end"
```

To increase the wait timeouts use the `LONG_WAIT` environment variable:

```
LONG_WAIT="100" pytest --no-header -s --disable-warnings --reuse-db -m "end_to_end"
```

You can also run the *frontend* tests in **headless** mode using the `HEADLESS` environment variable:

```
HEADLESS="True" pytest --no-header -s --disable-warnings --reuse-db -m "end_to_end"
```

You can also run tests without migrating the databases:

```
TESTS_NO_MIGRATIONS="True" pytest --no-header -vv -s -m "end_to_end"
```
