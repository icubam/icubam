from absl import logging  # noqa: F401
from icubam.db import store


class QueueWriter:
  """Processes an input queue and write the incoming data to DB."""
  def __init__(self, queue, db_factory):
    self.queue = queue
    self.db = db_factory.create()

  async def process(self):
    async for item in self.queue:
      try:
        user_id = item.pop('user_id', None)
        if user_id is None:
          logging.error("No user in request")
          return

        self.db.update_bed_count_for_icu(user_id, store.BedCount(**item))
      finally:
        self.queue.task_done()
