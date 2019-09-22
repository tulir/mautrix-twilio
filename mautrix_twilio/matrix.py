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
from typing import Optional
import asyncio

from mautrix.types import UserID, RoomID, Event, MessageEvent, StateEvent
from mautrix.appservice import AppService
from mautrix.bridge import BaseMatrixHandler

from .config import Config

from . import user as u, portal as po, puppet as pu


class MatrixHandler(BaseMatrixHandler):
    def __init__(self, az: AppService, config: Config,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        super(MatrixHandler, self).__init__(az, config, loop=loop)

    async def get_user(self, user_id: UserID) -> 'u.User':
        return u.User.get(user_id)

    async def get_portal(self, room_id: RoomID) -> 'po.Portal':
        return po.Portal.get_by_mxid(room_id)

    async def get_puppet(self, user_id: UserID) -> 'pu.Puppet':
        return pu.Puppet.get_by_mxid(user_id)

    @staticmethod
    async def allow_bridging_message(user: 'u.User', portal: 'po.Portal') -> bool:
        return user.is_whitelisted

    def filter_matrix_event(self, evt: Event) -> bool:
        if not isinstance(evt, (MessageEvent, StateEvent)):
            return True
        return (evt.sender == self.az.bot_mxid
                or pu.Puppet.get_twid_from_mxid(evt.sender) is not None)
