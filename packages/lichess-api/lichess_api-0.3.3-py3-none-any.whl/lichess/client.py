from typing import Literal

from . import schemas

from .schemas.custom.ApiStreamEvent import ApiStreamEvent
from .schemas.custom.BotGameStream import BotGameStream

from .session import TokenSession, Requestor

from .formats import JSON


# Base URL for the API
API_URL = "https://lichess.org"


class LichessClient:
    """
    Lichess Client

    :param token: Lichess Personal API access token, obtained from https://lichess.org/account/oauth/token
    :type token: `str`
    """

    def __init__(self, token: str, base_url=API_URL):
        self.token = token
        self.session = TokenSession(token)
        self._requestor = Requestor(self.session, base_url or API_URL, default_fmt=JSON)

    def stream_incoming_events(self):
        """
        Get your realtime stream of incoming events. See https://lichess.org/api#tag/Bot/operation/apiStreamEvent

        :return: stream of incoming events
        """
        path = "/api/stream/event"

        events = self._requestor.get(path, stream=True)

        for event in events:
            yield ApiStreamEvent.de_json(event)

    def stream_bot_game_state(self, game_id: str):
        """Get the stream of events for a bot game. See https://lichess.org/api#tag/Bot/operation/botGameStream

        :param game_id: ID of a game
        :type game_id: `str`
        :return: iterator over game states
        """
        path = f"/api/bot/game/stream/{game_id}"

        events = self._requestor.get(path, stream=True)

        for event in events:
            yield BotGameStream.de_json(event)

    def accept_challenge(self, challenge_id: str):
        """Accept an incoming challenge.

        :param challenge_id: ID of a challenge
        :type challenge_id: `str`
        """
        path = f"/api/challenge/{challenge_id}/accept"

        self._requestor.post(path)

    def decline_challenge(
        self,
        challenge_id: str,
        reason: Literal[
            "generic",
            "later",
            "tooFast",
            "tooSlow",
            "timeControl",
            "rated",
            "casual",
            "standard",
            "variant",
            "noBot",
            "onlyBot",
        ] = "generic",
    ):
        """Decline an incoming challenge.

        :param challenge_id: ID of a challenge
        :param reason: reason for declining challenge
        """
        path = f"/api/challenge/{challenge_id}/decline"
        payload = {"reason": reason}

        self._requestor.post(path, json=payload)

    def bot_write_game_chat_message(self, game_id: str, room: Literal["player", "spectator"], text: str):
        """Post a message in a bot game.

        :param game_id: ID of a game
        :type game_id: `str`
        :param room: "player" or "spectator"
        :param text: text of the message
        :type text: `str`
        """
        path = f"/api/bot/game/{game_id}/chat"

        payload = {"room": room, "text": text}

        self._requestor.post(path, json=payload)

    def make_bot_move(self, game_id: str, move: str):
        """Make a move in a bot game.

        :param game_id: ID of a game
        :type game_id: `str`
        :param move: The move to play, in UCI format
        """
        path = f"/api/bot/game/{game_id}/move/{move}"

        self._requestor.post(path)


# class FmtClient(BaseClient):
#     """Client that can return PGN or not.

#     :param session: request session, authenticated as needed
#     :param base_url: base URL for the API
#     :param pgn_as_default: ``True`` if PGN should be the default format for game exports
#         when possible. This defaults to ``False`` and is used as a fallback when
#         ``as_pgn`` is left as ``None`` for methods that support it.
#     """

#     def __init__(
#         self,
#         session: requests.Session,
#         base_url: str | None = None,
#         pgn_as_default: bool = False,
#     ):
#         super().__init__(session, base_url)
#         self.pgn_as_default = pgn_as_default

#     def _use_pgn(self, as_pgn: bool | None = None):
#         # helper to merge default with provided arg
#         return as_pgn if as_pgn is not None else self.pgn_as_default
