# Contributing

## Testing

### Unit tests

A few unit tests require `TOKEN_LOC` to be set with a valid `token.pickle` file in the `resources/icubam.env` file. If the `TOKEN_LOC` variable is not present, those tests will be skipped.

You also need to set the `JWT_SECRET` environement variable to any value e.g. `export JWT_SECRET="fakesecret"`.

Unit tests can be run with,
```
pytest
```

These will use only synthetic data.

By default all tests, not in the following categories
are unit tests and run with the above command.


### Integration tests

Integrations tests can be run with,

```
pytest -m integration --icubam-config=<config.toml path>
```
This will detect the database in the dev section of the config file,
make a copy of it to a temporary location and provide a new config object
with the `integration_config` pytest fixture. It can be used as follows,

```py
@pytest.mark.integration
def test_some_integration(integration_config):
    db_path = integration_config.db.sqlite_path
```

If ``--icubam-config`` key is not provided, the above test would be skipped.
If ``-m integration`` option is not provided, both unit and integration tests
are run (see [pytest
documentation](https://docs.pytest.org/en/latest/usage.html#specifying-tests-selecting-tests)
for more details).


### Frontend tests

Frontend tests can be run in two ways,

 1. Manually starting the services with,
    ```
    python scripts/run_server.py --server=all --config=<..>
    ```
    and then running
    ```
    pytest --icubam-config=<..> frontend_tests/
    ```
    
 2. Letting pytest start the web-services automatically with,
    ```
    pytest --icubam-config=<..>  --run-server frontend_tests/
    ```
    which is equivalent to two above steps. Web-services will be stopped at
    the end of the test session.

## Code style
The codebase is formatted using `yapf`. 

Running `yapf -i <filename>` will reformat a file in-place. Running `yapf -i -r .` at the root of the working copy will reformat the whole project in-place.

For convenience, there is a pre-commit hook available that will reject non-yapfing code.
The pre-commit additionally runs flake8 and mypy. 

Install [pre-commit](https://pre-commit.com/#install) to
run code style checks before each commit:

```
$ pip install pre-commit
$ pre-commit install
```

pre-commit checks can be
disabled for a particular commit with `git commit -n`.
