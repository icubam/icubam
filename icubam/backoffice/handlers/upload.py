"""Creating/edition of ICUs."""
from absl import logging
import io
import json
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import synchronizer


class UploadHandler(base.BaseHandler):
  ROUTE = "upload"

  def answer(self, msg, error=False):
    logging.error(msg)
    self.write(json.dumps({'msg': msg, 'error': error}))

  @tornado.web.authenticated
  def post(self):
    try:
      data = json.loads(self.request.body.decode())
    except Exception as e:
      return self.answer(f'Could not upload json {e}', error=True)

    content = data.get('data', None)
    if content is None:
      return self.answer(f'No CSV content', error=True)

    sync = synchronizer.CSVSynchronizer(self.db)
    sync_fns = {
      'user': sync.sync_users_from_csv,
      'icu': sync.sync_icus_from_csv,
      'bedcounts': sync.sync_bedcount_from_csv
    }
    objtype = data.get('objtype', None)
    sync_fn = sync_fns.get(objtype, None)
    if sync_fn is None:
      return self.answer(
        'Cannot find proper synchronization method.', error=True
      )

    try:
      num_updates = sync_fn(io.StringIO(content), force_update=True)
      return self.answer(f'Updated {num_updates} {objtype}')
    except:
      return self.answer('Failing while syncing csv content', error=True)
