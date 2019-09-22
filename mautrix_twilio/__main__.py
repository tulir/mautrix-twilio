# mautrix-twilio - A Matrix-Twilio relaybot bridge.
# Copyright (C) 2019 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from mautrix.bridge import Bridge

from .config import Config
from .twilio import TwilioHandler, TwilioClient
from .matrix import MatrixHandler
from .sqlstatestore import SQLStateStore
from .context import Context
from .puppet import init as init_puppet
from .portal import init as init_portal
from .user import init as init_user
from .db import init as init_db
from . import __version__


class TwilioBridge(Bridge):
    name = "mautrix-twilio"
    command = "python -m mautrix-twilio"
    description = "A Matrix-Twilio relaybot bridge."
    version = __version__
    config_class = Config
    matrix_class = MatrixHandler
    state_store_class = SQLStateStore

    config: Config
    twilio: TwilioHandler
    twilio_client: TwilioClient

    def prepare_bridge(self) -> None:
        init_db(self.db)
        self.twilio_client = TwilioClient(config=self.config, loop=self.loop)
        context = Context(az=self.az, config=self.config, twc=self.twilio_client, loop=self.loop)
        context.mx = self.matrix = MatrixHandler(self.az, self.config, self.loop)
        context.tw = self.twilio = TwilioHandler(context)
        init_user(context)
        init_portal(context)
        init_puppet(context)
        self.az.app.add_subapp(self.config["twilio.webhook_path"], self.twilio.app)


TwilioBridge().run()
