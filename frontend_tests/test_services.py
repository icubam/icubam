import pytest
from urllib.request import urlopen


@pytest.mark.parametrize('server', ['server', 'messaging', 'backoffice'])
def test_health_urls(integration_config, icubam_services_fx, server):
  cfg = integration_config

  if server == 'backoffice':
    base_url = "{}{}/".format(
      cfg['server'].base_url.replace(
        str(cfg['server'].port), str(cfg['backoffice'].port)
      ), cfg['backoffice'].root.strip('/')
    )
  else:
    base_url = cfg[server].base_url
  res = urlopen(base_url + 'health')
  assert res.getcode() == 200
