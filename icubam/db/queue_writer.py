from absl import logging
from icubam.db import store

class QueueWriter:
  """Processes an input queue and write the incoming data to DB."""

  def __init__(self, queue, db):
    self.queue = queue
    self.db = db

  async def process(self):
    async for item in self.queue:
      try:
        icu_id = item.pop('icu_id', None)
        if icu_id is None:
          logging.error('Missing ICU in {}'.format(item))
        item.pop('icu_name', None)
        print(item)
        self.db.update_bed_count_for_icu(icu_id, store.BedCount(**item))
      finally:
        self.queue.task_done()
