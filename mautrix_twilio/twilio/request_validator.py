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

# This is based on https://github.com/twilio/twilio-python/blob/master/twilio/request_validator.py
# with changes to remove antiquated python support and use yarl for all URL processing.

from typing import Dict, Union
from hashlib import sha1, sha256
import base64
import hmac

from yarl import URL


class RequestValidator:
    def __init__(self, token: str) -> None:
        self.token = token.encode("utf-8")

    def _compute_signature(self, url: URL, params: Dict[str, str]) -> bytes:
        """
        Compute the signature for a given request.

        Args:
            url: Full URI that Twilio requested on your server.
            params: Dictionary of POST variables.

        Returns:
            The computed signature.
        """
        signature_data = str(url)
        for key, value in sorted(params.items()):
            signature_data += key + value
        return hmac.new(self.token, signature_data.encode("utf-8"), sha1).digest()

    @staticmethod
    def _compute_hash(body) -> str:
        """
        Compute the SHA256 hash for the given data.

        Args:
            body: The request body.

        Returns:
            The hex-formatted sha256 hash.
        """
        return sha256(body.encode("utf-8")).hexdigest().strip()

    def validate(self, url: URL, params: Union[str, bytes, Dict[str, str]],
                 signature: str) -> bool:
        """
        Validate a request from Twilio.

        Args:
            url: Full URI that Twilio requested on your server.
            params: Dictionary of POST variables or string of POST body for JSON requests.
            signature: The signature in the X-Twilio-Signature header.

        Returns:
            True if the request passes validation, False if not.
        """

        url = url.with_scheme("https").with_port(None)
        try:
            decoded_signature = base64.b64decode(signature)
        except Exception:
            return False

        if "bodySHA256" in url.query and isinstance(params, (str, bytes)):
            valid_body_hash = hmac.compare_digest(self._compute_hash(params),
                                                  url.query["bodySHA256"])
            valid_signature = hmac.compare_digest(self._compute_signature(url, {}),
                                                  decoded_signature)
            return valid_body_hash and valid_signature
        else:
            return hmac.compare_digest(self._compute_signature(url, params or {}),
                                       decoded_signature)
