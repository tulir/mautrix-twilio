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
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Boolean
from sqlalchemy.sql import expression

from mautrix.util.db import Base

if TYPE_CHECKING:
    from ..twilio import TwilioUserID


class Puppet(Base):
    __tablename__ = "puppet"

    twid: 'TwilioUserID' = Column(String(127), primary_key=True)
    matrix_registered: bool = Column(Boolean, nullable=False, server_default=expression.false())

    @classmethod
    def get_by_twid(cls, twid: 'TwilioUserID') -> Optional['Puppet']:
        return cls._select_one_or_none(cls.c.twid == twid)
