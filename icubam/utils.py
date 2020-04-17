import icubam
from absl import logging


def maybe_init_sentry(cfg, server_name=None):
  """Enable Sentry SDK if module available and SENTRY_URL set."""
  if not cfg.SENTRY_URL:
    logging.info(f"Not loading Sentry as cfg.SENTRY_URL not loaded.")
    return
  try:
    import sentry_sdk
    from sentry_sdk.integrations.tornado import TornadoIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    release = f'ICUBAM-{server_name}-{icubam.__version__}'
    sentry_sdk.init(
      environment=cfg.SENTRY_ENV,
      release=release,
      dsn=cfg.SENTRY_URL,
      integrations=[TornadoIntegration(),
                    SqlalchemyIntegration()]
    )
    logging.info(f"Initialised sentry on {cfg.SENTRY_ENV}, release {release}.")
  except ModuleNotFoundError as e:
    logging.info(f"Not loading sentry: {e}")
