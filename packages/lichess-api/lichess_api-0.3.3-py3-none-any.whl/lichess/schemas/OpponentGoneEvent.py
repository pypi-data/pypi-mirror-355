from typing import Literal

from ._internal import JsonDeserializable


class OpponentGoneEvent(JsonDeserializable):
    """
    OpponentGoneEvent

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/OpponentGoneEvent.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(
        self, type: Literal["opponentGone"], gone: bool, claimWinInSeconds: int | None = None, **kwargs
    ):
        self.type: Literal["opponentGone"] = type
        self.gone = gone
        self.claimWinInSeconds = claimWinInSeconds
