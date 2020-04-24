import pytest
from urllib.request import urlopen


@pytest.mark.parametrize('server', ['server', 'messaging', 'backoffice'])
def test_health_urls(integration_config, icubam_services_fx, server):
  cfg = integration_config

  if server in ['server', 'messaging']:
    res = urlopen(cfg[server].base_url + 'health')
    assert res.getcode() == 200
  else:
    backoffice_url = 'http://localhost:{}/{}/'.format(
      cfg['backoffice'].port, cfg['backoffice'].root
    )
    res = urlopen(backoffice_url)
    assert res.getcode() == 200
