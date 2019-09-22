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
from typing import Optional, Iterable, TYPE_CHECKING

from sqlalchemy import Column, String, and_

from mautrix.util.db import Base
from mautrix.types import RoomID, EventID

if TYPE_CHECKING:
    from ..twilio import TwilioUserID, TwilioMessageID


class Message(Base):
    __tablename__ = "message"

    mxid: EventID = Column(String(255))
    mx_room: RoomID = Column(String(255))
    tw_receiver: 'TwilioUserID' = Column(String(127), primary_key=True)
    twid: 'TwilioMessageID' = Column(String(127), primary_key=True)

    @classmethod
    def get_all_by_twid(cls, twid: 'TwilioMessageID', tw_receiver: 'TwilioUserID'
                        ) -> Iterable['Message']:
        return cls._select_all(cls.c.twid == twid, cls.c.tw_receiver == tw_receiver)

    @classmethod
    def get_by_twid(cls, twid: 'TwilioMessageID', tw_receiver: 'TwilioUserID'
                    ) -> Optional['Message']:
        return cls._select_one_or_none(and_(cls.c.twid == twid, cls.c.tw_receiver == tw_receiver))

    @classmethod
    def get_by_mxid(cls, mxid: EventID, mx_room: RoomID) -> Optional['Message']:
        return cls._select_one_or_none(and_(cls.c.mxid == mxid, cls.c.mx_room == mx_room))
