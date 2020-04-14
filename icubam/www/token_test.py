from icubam.www import token
from icubam import config


def test_encode():
  cfg = config.Config('resources/test.toml')
  tkn = token.TokenEncoder(cfg)
  userid = 1234
  encoded = tkn.encode(userid)
  assert isinstance(encoded, str)
  assert tkn.decode(encoded) == userid
