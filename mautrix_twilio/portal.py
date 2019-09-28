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
from typing import Dict, Optional, List, Any, TYPE_CHECKING
from string import Template
from html import escape
import mimetypes
import asyncio

from mautrix.types import (RoomID, UserID, EventID, EventType, StrippedStateEvent, MessageType,
                           MessageEventContent, TextMessageEventContent, Format, FileInfo,
                           MediaMessageEventContent, PowerLevelStateEventContent)
from mautrix.bridge import BasePortal
from mautrix.appservice import IntentAPI

from .db import Portal as DBPortal, Message as DBMessage
from .twilio import (TwilioUserID, TwilioMessageID, TwilioClient, TwilioMessageEvent,
                     TwilioStatusEvent, TwilioMessageStatus)
from .formatter import whatsapp_to_matrix, matrix_to_whatsapp
from . import puppet as p, user as u

if TYPE_CHECKING:
    from .context import Context


class Portal(BasePortal):
    homeserver_address: str
    message_template: Template
    bridge_notices: bool
    federate_rooms: bool
    invite_users: List[UserID]
    initial_state: Dict[str, Dict[str, Any]]

    twc: TwilioClient

    by_mxid: Dict[RoomID, 'Portal'] = {}
    by_twid: Dict[TwilioUserID, 'Portal'] = {}

    twid: TwilioUserID
    mxid: Optional[RoomID]

    _db_instance: DBPortal

    _main_intent: Optional[IntentAPI]
    _create_room_lock: asyncio.Lock
    _send_lock: asyncio.Lock

    def __init__(self, twid: TwilioUserID, mxid: Optional[RoomID] = None,
                 db_instance: Optional[DBPortal] = None) -> None:
        super().__init__()
        self.twid = twid
        self.mxid = mxid

        self._db_instance = db_instance
        self._main_intent = None
        self._create_room_lock = asyncio.Lock()
        self._send_lock = asyncio.Lock()
        self.log = self.log.getChild(self.twid)

        self.by_twid[self.twid] = self
        if self.mxid:
            self.by_mxid[self.mxid] = self

    @property
    def db_instance(self) -> DBPortal:
        if not self._db_instance:
            self._db_instance = DBPortal(twid=self.twid, mxid=self.mxid)
        return self._db_instance

    @classmethod
    def from_db(cls, db_portal: DBPortal) -> 'Portal':
        return Portal(twid=db_portal.twid, mxid=db_portal.mxid, db_instance=db_portal)

    def save(self) -> None:
        self.db_instance.edit(mxid=self.mxid)

    def delete(self) -> None:
        self.by_twid.pop(self.twid, None)
        self.by_mxid.pop(self.mxid, None)
        if self._db_instance:
            self._db_instance.delete()

    @property
    def main_intent(self) -> IntentAPI:
        if not self._main_intent:
            self._main_intent = p.Puppet.get_by_twid(self.twid).intent
        return self._main_intent

    async def create_matrix_room(self) -> RoomID:
        if self.mxid:
            return self.mxid
        async with self._create_room_lock:
            try:
                return await self._create_matrix_room()
            except Exception:
                self.log.exception("Failed to create portal")

    async def _create_matrix_room(self) -> RoomID:
        if self.mxid:
            return self.mxid

        self.log.debug("Creating Matrix room")
        puppet = p.Puppet.get_by_twid(self.twid)
        await puppet.update_displayname()
        creation_content = {
            "m.federate": self.federate_rooms
        }
        initial_state = {EventType.find(event_type): StrippedStateEvent.deserialize({
            "type": event_type,
            "state_key": "",
            "content": content
        }) for event_type, content in self.initial_state.items()}
        if EventType.ROOM_POWER_LEVELS not in initial_state:
            initial_state[EventType.ROOM_POWER_LEVELS] = StrippedStateEvent(
                type=EventType.ROOM_POWER_LEVELS, content=PowerLevelStateEventContent())
        plc = initial_state[EventType.ROOM_POWER_LEVELS].content
        plc.users[self.az.bot_mxid] = 100
        plc.users[self.main_intent] = 100
        for user_id in self.invite_users:
            plc.users.setdefault(user_id, 100)
        self.mxid = await self.main_intent.create_room(name=puppet.displayname,
                                                       invitees=[self.az.bot_mxid,
                                                                 *self.invite_users],
                                                       creation_content=creation_content,
                                                       initial_state=list(initial_state.values()))
        if not self.mxid:
            raise Exception("Failed to create room: no mxid received")
        self.save()
        self.log.debug(f"Matrix room created: {self.mxid}")
        self.by_mxid[self.mxid] = self
        await self.main_intent.join_room_by_id(self.mxid)
        return self.mxid

    async def handle_twilio_message(self, message: TwilioMessageEvent) -> None:
        if not await self.create_matrix_room():
            return
        mxid = None

        if message.media:
            resp = await self.az.http_session.get(message.media.url)
            data = await resp.read()
            mime = message.media.mime_type
            mxc = await self.main_intent.upload_media(data, mime)
            msgtype = MessageType.FILE
            if mime.startswith("image/"):
                msgtype = MessageType.IMAGE
            elif mime.startswith("video/"):
                msgtype = MessageType.VIDEO
            elif mime.startswith("audio/"):
                msgtype = MessageType.AUDIO
            ext = mimetypes.guess_extension(mime)
            content = MediaMessageEventContent(body=f"{message.id}{ext}", msgtype=msgtype, url=mxc,
                                               info=FileInfo(size=len(data), mimetype=mime))
            mxid = await self.main_intent.send_message(self.mxid, content)

        if message.body:
            html, text = whatsapp_to_matrix(message.body)
            content = TextMessageEventContent(msgtype=MessageType.TEXT, body=text)
            if html is not None:
                content.format = Format.HTML
                content.formatted_body = html
            mxid = await self.main_intent.send_message(self.mxid, content)

        if not mxid:
            mxid = await self.main_intent.send_notice(self.mxid, "Message with unknown content")

        msg = DBMessage(mxid=mxid, mx_room=self.mxid, tw_receiver=self.twid, twid=message.id)
        msg.insert()

    async def handle_twilio_status(self, status: TwilioStatusEvent) -> None:
        if not self.mxid:
            return
        async with self._send_lock:
            msg = DBMessage.get_by_twid(status.id, self.twid)
            if status.status == TwilioMessageStatus.DELIVERED:
                await self.az.intent.mark_read(self.mxid, msg.mxid)
            elif status.status == TwilioMessageStatus.READ:
                await self.main_intent.mark_read(self.mxid, msg.mxid)
            elif status.status == TwilioMessageStatus.UNDELIVERED:
                await self.az.intent.react(self.mxid, msg.mxid, "\u274c")
            elif status.status == TwilioMessageStatus.FAILED:
                await self.az.intent.react(self.mxid, msg.mxid, "\u274c")

    async def handle_matrix_message(self, sender: 'u.User', message: MessageEventContent,
                                    event_id: EventID) -> None:
        async with self._send_lock:
            if message.msgtype == MessageType.TEXT or (message.msgtype == MessageType.NOTICE
                                                       and self.bridge_notices):
                localpart, _ = self.az.intent.parse_user_id(sender.mxid)
                html = (message.formatted_body if message.format == Format.HTML
                        else escape(message.body))
                html = self.message_template.safe_substitute(
                    message=html, mxid=sender.mxid, localpart=localpart,
                    displayname=await self.az.intent.get_room_displayname(self.mxid, sender.mxid))
                text = matrix_to_whatsapp(html)
                resp = await self.twc.send_message(self.twid, text)
            elif message.msgtype in (MessageType.AUDIO, MessageType.VIDEO, MessageType.IMAGE,
                                     MessageType.FILE):
                url = f"{self.homeserver_address}/_matrix/media/r0/download/{message.url[6:]}"
                resp = await self.twc.send_message(self.twid, media=url)
            else:
                self.log.debug(f"Ignoring unknown message {message}")
                return
            self.log.debug(f"Twilio send response: {resp}")
            DBMessage(mxid=event_id, mx_room=self.mxid, tw_receiver=self.twid,
                      twid=TwilioMessageID(resp["sid"])).insert()

    @classmethod
    def get_by_mxid(cls, mxid: RoomID) -> Optional['Portal']:
        try:
            return cls.by_mxid[mxid]
        except KeyError:
            pass

        db_portal = DBPortal.get_by_mxid(mxid)
        if db_portal:
            return cls.from_db(db_portal)

        return None

    @classmethod
    def get_by_twid(cls, twid: TwilioUserID, create: bool = True) -> Optional['Portal']:
        try:
            return cls.by_twid[twid]
        except KeyError:
            pass

        db_portal = DBPortal.get_by_twid(twid)
        if db_portal:
            return cls.from_db(db_portal)

        if create:
            portal = cls(twid=twid)
            portal.db_instance.insert()
            return portal

        return None


def init(context: 'Context') -> None:
    Portal.az, config, Portal.loop = context.core
    Portal.twc = context.twc
    Portal.homeserver_address = config["homeserver.public_address"]
    Portal.message_template = Template(config["bridge.message_template"])
    Portal.bridge_notices = config["bridge.bridge_notices"]
    Portal.federate_rooms = config["bridge.federate_rooms"]
    Portal.invite_users = config["bridge.invite_users"]
    Portal.initial_state = config["bridge.initial_state"]
