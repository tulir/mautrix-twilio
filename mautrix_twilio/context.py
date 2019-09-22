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
from typing import Optional, Tuple, TYPE_CHECKING
from asyncio import AbstractEventLoop

from mautrix.appservice import AppService

from .config import Config

if TYPE_CHECKING:
    from .matrix import MatrixHandler
    from .twilio import TwilioHandler, TwilioClient


class Context:
    az: AppService
    config: Config
    twc: 'TwilioClient'
    loop: AbstractEventLoop
    mx: Optional['MatrixHandler']
    tw: Optional['TwilioHandler']

    def __init__(self, az: AppService, config: Config, twc: 'TwilioClient', loop: AbstractEventLoop
                 ) -> None:
        self.az = az
        self.config = config
        self.twc = twc
        self.loop = loop
        self.mx = None
        self.tw = None

    @property
    def core(self) -> Tuple[AppService, Config, AbstractEventLoop]:
        return self.az, self.config, self.loop
