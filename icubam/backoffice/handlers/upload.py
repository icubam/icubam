"""Creating/edition of ICUs."""
from absl import logging
import io
import json
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import synchronizer
from typing import Dict, Callable


class UploadHandler(base.BaseHandler):
  ROUTE = "upload"

  def answer(self, msg, error=False) -> None:
    logging.error(msg)
    self.write(json.dumps({'msg': msg, 'error': error}))

  @tornado.web.authenticated
  def post(self) -> None:
    try:
      data = json.loads(self.request.body.decode())
    except Exception as e:
      return self.answer(f'Could not upload json {e}', error=True)

    content = data.get('data', None)
    if content is None:
      return self.answer('No CSV content', error=True)

    sync = synchronizer.CSVSynchronizer(self.db)
    sync_fns: Dict[base.ObjType, Callable[..., int]] = {
      base.ObjType.USERS: sync.sync_users_from_csv,
      base.ObjType.ICUS: sync.sync_icus_from_csv,
      base.ObjType.BEDCOUNTS: sync.sync_bedcounts_from_csv
    }
    objtype_name = data.get('objtype', None)
    try:
      objtype = base.ObjType[objtype_name]
      sync_fn = sync_fns[objtype]
    except KeyError:
      return self.answer(
        'Cannot find proper synchronization method.', error=True
      )

    try:
      num_updates = sync_fn(io.StringIO(content), force_update=True)
      return self.answer(f'Updated {num_updates} {objtype}')
    except:
      return self.answer('Failing while syncing csv content', error=True)
