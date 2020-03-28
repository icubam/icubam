from absl import app
from absl import flags
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from icubam import config
from icubam.model.user import Base, User

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode)

  engine = create_engine("sqlite+pysqlite:///{}".format(cfg.db.sqlite_path), encoding='utf-8', echo=True)
  metadata = Base.metadata
  metadata.create_all(engine)

  user = User(name="admin")
  Session = sessionmaker(bind=engine)
  session = Session()
  session.add(user)
  session.commit()
  session.close()


if __name__ == "__main__":
  app.run(main)
