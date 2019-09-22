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
from typing import NewType

import attr
from attr import dataclass

from mautrix.types import SerializableAttrs, SerializableEnum

TwilioMessageID = NewType('TwilioMessageID', str)
TwilioUserID = NewType('TwilioUserID', str)
TwilioAccountID = NewType('TwilioAccountID', str)


class TwilioEventType(SerializableEnum):
    DELIVERED = "DELIVERED"
    READ = "READ"
    UNDELIVERED = "UNDELIVERED"


class TwilioMessageStatus(SerializableEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RECEIVED = "received"
    UNDELIVERED = "undelivered"


@dataclass
class TwilioMedia(SerializableAttrs['TwilioMedia']):
    mime_type: str = attr.ib(default=None, metadata={"json": "MediaContentType0"})
    url: str = attr.ib(default=None, metadata={"json": "MediaUrl0"})


@dataclass
class TwilioMessageEvent(SerializableAttrs['TwilioEvent']):
    id: TwilioMessageID = attr.ib(metadata={"json": "MessageSid"})
    receiver: TwilioUserID = attr.ib(metadata={"json": "To"})
    sender: TwilioUserID = attr.ib(metadata={"json": "From"})
    status: TwilioMessageStatus = attr.ib(metadata={"json": "SmsStatus"})

    body: str = attr.ib(metadata={"json": "Body"})
    segments: str = attr.ib(metadata={"json": "NumSegments"})
    media: TwilioMedia = attr.ib(default=None, metadata={"flatten": True})


@dataclass
class TwilioStatusEvent(SerializableAttrs['TwilioEvent']):
    id: TwilioMessageID = attr.ib(metadata={"json": "MessageSid"})
    receiver: TwilioUserID = attr.ib(metadata={"json": "To"})
    sender: TwilioUserID = attr.ib(metadata={"json": "From"})
    status: TwilioMessageStatus = attr.ib(metadata={"json": "SmsStatus"})

    event_type: TwilioEventType = attr.ib(default=None, metadata={"json": "EventType"})
