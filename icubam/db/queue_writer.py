from absl import logging  # noqa: F401
from icubam.db import store

class QueueWriter:
  """Processes an input queue and write the incoming data to DB."""

  def __init__(self, queue, db):
    self.queue = queue
    self.db = db

  async def process(self):
    async for item in self.queue:
      try:
        item.pop('icu_name', None)
        # Here we do not necessarily have acccess to the user.
        # We force the update.
        # TODO(olivier): should we send the user id in the token?
        self.db.update_bed_count_for_icu(
          None, store.BedCount(**item), force=True)
      finally:
        self.queue.task_done()
