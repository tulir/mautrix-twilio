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
from typing import Optional, Dict, TYPE_CHECKING

from mautrix.types import UserID
from mautrix.bridge import BasePuppet
from mautrix.util.simple_template import SimpleTemplate

from .config import Config
from .db import Puppet as DBPuppet
from .twilio import TwilioUserID

if TYPE_CHECKING:
    from .context import Context

config: Config


class Puppet(BasePuppet):
    hs_domain: str
    twid_template: SimpleTemplate[int] = SimpleTemplate("whatsapp:+{number}", "number", type=int)
    mxid_template: SimpleTemplate[str]
    displayname_template: SimpleTemplate[str]

    by_twid: Dict[TwilioUserID, 'Puppet'] = {}

    twid: TwilioUserID

    _db_instance: Optional[DBPuppet]

    def __init__(self, twid: TwilioUserID, is_registered: bool = False,
                 db_instance: Optional[DBPuppet] = None) -> None:
        super().__init__()
        self.twid = twid
        self.is_registered = is_registered
        self._db_instance = db_instance
        self.intent = self.az.intent.user(self.mxid)
        self.log = self.log.getChild(self.twid)
        self.by_twid[self.twid] = self

    @property
    def phone_number(self) -> int:
        return self.twid_template.parse(self.twid)

    @property
    def mxid(self) -> UserID:
        return UserID(self.mxid_template.format_full(str(self.phone_number)))

    @property
    def displayname(self) -> str:
        return self.displayname_template.format_full(str(self.phone_number))

    @property
    def db_instance(self) -> DBPuppet:
        if not self._db_instance:
            self._db_instance = DBPuppet(twid=self.twid, matrix_registered=self.is_registered)
        return self._db_instance

    @classmethod
    def from_db(cls, db_puppet: DBPuppet) -> 'Puppet':
        return cls(twid=db_puppet.twid, is_registered=db_puppet.matrix_registered,
                   db_instance=db_puppet)

    def save(self) -> None:
        self.db_instance.edit(matrix_registered=self.is_registered)

    async def update_displayname(self) -> None:
        await self.intent.set_displayname(self.displayname)

    @classmethod
    def get_by_twid(cls, twid: TwilioUserID, create: bool = True) -> Optional['Puppet']:
        print("GET BY TWID", twid)
        try:
            return cls.by_twid[twid]
        except KeyError:
            pass

        db_puppet = DBPuppet.get_by_twid(twid)
        if db_puppet:
            return cls.from_db(db_puppet)

        if create:
            puppet = cls(twid)
            puppet.db_instance.insert()
            return puppet

        return None

    @classmethod
    def get_by_mxid(cls, mxid: UserID, create: bool = True) -> Optional['Puppet']:
        print("GET BY MXID", mxid)
        twid = cls.get_twid_from_mxid(mxid)
        if twid:
            return cls.get_by_twid(twid, create)

        return None

    @classmethod
    def get_twid_from_mxid(cls, mxid: UserID) -> Optional[TwilioUserID]:
        return cls.mxid_template.parse(mxid)

    @classmethod
    def get_mxid_from_twid(cls, twid: TwilioUserID) -> UserID:
        return UserID(cls.mxid_template.format_full(str(cls.twid_template.parse(twid))))


def init(context: 'Context') -> None:
    global config
    Puppet.az, config, Puppet.loop = context.core
    Puppet.mx = context.mx
    Puppet.hs_domain = config["homeserver"]["domain"]
    Puppet.mxid_template = SimpleTemplate(config["bridge.username_template"], "userid",
                                          prefix="@", suffix=f":{Puppet.hs_domain}", type=str)
    Puppet.displayname_template = SimpleTemplate(config["bridge.displayname_template"],
                                                 "displayname", type=str)
