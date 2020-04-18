# Contributing

## Testing

### Unit tests

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
