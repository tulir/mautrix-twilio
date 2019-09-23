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
from typing import cast

from mautrix.util.formatter import (MatrixParser as BaseMatrixParser, MarkdownString, EntityType)


def matrix_to_whatsapp(html: str) -> str:
    return MatrixParser.parse(html).text


class WhatsAppFormatString(MarkdownString):
    def format(self, entity_type: EntityType, **kwargs) -> 'WhatsAppFormatString':
        prefix = suffix = ""
        if entity_type == EntityType.BOLD:
            prefix = suffix = "*"
        elif entity_type == EntityType.ITALIC:
            prefix = suffix = "_"
        elif entity_type == EntityType.STRIKETHROUGH:
            prefix = suffix = "~"
        elif entity_type == EntityType.URL:
            if kwargs['url'] != self.text:
                suffix = f" ({kwargs['url']})"
        elif entity_type in (EntityType.PREFORMATTED, EntityType.INLINE_CODE):
            prefix = suffix = "```"
        elif entity_type == EntityType.BLOCKQUOTE:
            children = self.trim().split("\n")
            children = [child.prepend("> ") for child in children]
            return self.join(children, "\n")
        elif entity_type == EntityType.HEADER:
            prefix = "#" * kwargs["size"] + " "
        else:
            return self

        self.text = f"{prefix}{self.text}{suffix}"
        return self


class MatrixParser(BaseMatrixParser[WhatsAppFormatString]):
    fs = WhatsAppFormatString

    @classmethod
    def parse(cls, data: str) -> WhatsAppFormatString:
        return cast(WhatsAppFormatString, super().parse(data))

