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
from typing import Dict, Optional, TYPE_CHECKING

from mautrix.types import UserID
from mautrix.bridge import BaseUser

from . import puppet as pu
from .config import Config

if TYPE_CHECKING:
    from .context import Context

config: Config


class User(BaseUser):
    by_mxid: Dict[UserID, 'User'] = {}

    is_whitelisted: bool
    is_admin: bool

    def __init__(self, mxid: UserID) -> None:
        super().__init__()
        self.mxid = mxid
        self.by_mxid[self.mxid] = self
        self.command_status = None
        self.is_whitelisted, self.is_admin = config.get_permissions(self.mxid)
        self.log = self.log.getChild(self.mxid)

    @classmethod
    def get(cls, mxid: UserID) -> Optional['User']:
        if pu.Puppet.get_twid_from_mxid(mxid) is not None or mxid == cls.az.bot_mxid:
            return None
        try:
            return cls.by_mxid[mxid]
        except KeyError:
            return cls(mxid)


def init(context: 'Context') -> None:
    global config
    User.az, config, User.loop = context.core
