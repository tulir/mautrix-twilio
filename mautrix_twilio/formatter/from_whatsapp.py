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
from typing import Match, Tuple, Optional
import re

italic = re.compile(r"([\s>~*]|^)_(.+?)_([^a-zA-Z\d]|$)")
bold = re.compile(r"([\s>_~]|^)\*(.+?)\\*([^a-zA-Z\d]|$)")
strike = re.compile(r"([\s>_*]|^)~(.+?)~([^a-zA-Z\d]|$)")
code_block = re.compile("```((?:.|\n)+?)```")


def code_block_repl(match: Match) -> str:
    text = match.group(1)
    if "\n" in text:
        return f"<pre><code>{text}</code></pre>"
    return f"<code>{text}</code>"


def whatsapp_to_matrix(text: str) -> Tuple[Optional[str], str]:
    html = italic.sub(r"\1<em>\2</em>\3", text)
    html = bold.sub(r"\1<strong>\2</strong>\3", html)
    html = strike.sub(r"\1<del>\2</del>\3", html)
    html = code_block.sub(code_block_repl, html)
    if html != text:
        return html.replace("\n", "<br/>"), text
    return None, text
