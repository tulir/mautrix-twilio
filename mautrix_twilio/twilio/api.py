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
from typing import Dict, Optional
import asyncio
import logging

from aiohttp import ClientSession, BasicAuth

from .data import TwilioUserID, TwilioAccountID
from ..config import Config


class TwilioClient:
    log: logging.Logger = logging.getLogger("mau.twilio.api")
    base_url: str = "https://api.twilio.com/2010-04-01"
    http: ClientSession
    sender_id: TwilioUserID
    account_id: TwilioAccountID

    def __init__(self, config: Config, loop: asyncio.AbstractEventLoop) -> None:
        self.sender_id = config["twilio.sender_id"]
        self.account_id = config["twilio.account_id"]
        self.http = ClientSession(loop=loop, auth=BasicAuth(self.account_id,
                                                            config["twilio.secret"]))

    async def send_message(self, receiver: TwilioUserID, body: Optional[str] = None,
                           media: Optional[str] = None) -> Dict[str, str]:
        data = {
            "From": self.sender_id,
            "To": receiver,
        }
        if body:
            data["Body"] = body
        if media:
            data["MediaUrl"] = media
        self.log.debug(f"Sending message {data}")
        resp = await self.http.post(f"{self.base_url}/Accounts/{self.account_id}/Messages.json",
                                    data=data)
        return await resp.json()
