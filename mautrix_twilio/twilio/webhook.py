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
from typing import Optional, Tuple, Any, TYPE_CHECKING
import logging
import asyncio

from aiohttp import web

from .request_validator import RequestValidator
from .data import TwilioMessageEvent, TwilioStatusEvent
from .. import portal as po

if TYPE_CHECKING:
    from ..context import Context


class TwilioHandler:
    log: logging.Logger = logging.getLogger("twilio.in")
    app: web.Application
    validator: RequestValidator

    def __init__(self, context: 'Context') -> None:
        self.loop = context.loop or asyncio.get_event_loop()
        self.app = web.Application(loop=self.loop)
        self.app.router.add_route("POST", "/receive", self.receive)
        self.app.router.add_route("POST", "/status", self.status)
        self.validator = RequestValidator(token=context.config["twilio.secret"])

    async def _validate_request(self, request: web.Request, type_class: Any
                                ) -> Tuple[Any, Optional[web.Response]]:
        data = dict(**await request.post())
        try:
            signature = request.headers["X-Twilio-Signature"]
        except KeyError:
            return None, web.Response(status=400, text="Missing signature")
        is_valid = self.validator.validate(request.url, data, signature)
        if not is_valid:
            return None, web.Response(status=401, text="Invalid signature")
        return type_class.deserialize(data), None

    async def receive(self, request: web.Request) -> web.Response:
        data, err = await self._validate_request(request, TwilioMessageEvent)
        if err is not None:
            return err
        self.log.debug(f"Received Twilio message event: {data}")
        portal = po.Portal.get_by_twid(data.sender)
        await portal.handle_twilio_message(data)
        return web.Response(status=204)

    async def status(self, request: web.Request) -> web.Response:
        data, err = await self._validate_request(request, TwilioStatusEvent)
        if err is not None:
            return err
        self.log.debug(f"Received Twilio status event: {data}")
        portal = po.Portal.get_by_twid(data.receiver)
        await portal.handle_twilio_status(data)
        return web.Response(status=204)
