from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

import sys
from os.path import abspath, dirname

sys.path.insert(0, dirname(dirname(abspath(__file__))))

from mautrix.util.db import Base
from mautrix_twilio.config import Config
import mautrix_twilio.db

config = context.config
mxtw_config_path = context.get_x_argument(as_dictionary=True).get("config", "config.yaml")
mxtw_config = Config(mxtw_config_path, None, None)
mxtw_config.load()
config.set_main_option("sqlalchemy.url",
                       mxtw_config.get("appservice.database", "sqlite:///mautrix-twilio.db"))
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
