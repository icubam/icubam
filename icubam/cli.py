from absl import logging
import multiprocessing as mp

from icubam.backoffice import server as backoffice_server
from icubam.messaging import server as msg_server
from icubam.www import server as www_server


def run_one_server(cls, cfg, port=None):
  logging.set_verbosity(logging.INFO)
  cls(cfg, port).run()


def run_server(cfg, server="www", port=None):
  """Start ICUBAM web-services
  
  Returns:
    list of started processes if server=="all", None otherwise
  
  """
  servers = {
    'www': www_server.WWWServer,
    'message': msg_server.MessageServer,
    'backoffice': backoffice_server.BackOfficeServer,
  }
  service = servers.get(server, None)
  if service is not None:
    run_one_server(service, cfg, port)
  elif server == 'all':
    processes = [
      mp.Process(target=run_one_server, args=(cls, cfg))
      for cls in servers.values()
    ]
    for p in processes:
      p.start()
    return processes
