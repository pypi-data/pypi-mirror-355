from typing import Literal

from ._internal import JsonDeserializable

from .ChallengeStatus import ChallengeStatus
from .Variant import Variant
from .Speed import Speed
from .TimeControl import TimeControl
from .GameColor import GameColor


class ChallengeOpenJson(JsonDeserializable):
    """
    ChallengeOpenJson

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/ChallengeOpenJson.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string)
        if "variant" in obj:
            obj["variant"] = Variant.de_json(obj.get("variant"))
        if "timeControl" in obj:
            obj["timeControl"] = TimeControl.de_json(obj.get("timeControl"))
        return cls(**obj)

    def __init__(
        self,
        *,
        id: str,
        url: str,
        status: ChallengeStatus,
        challenger: None,
        destUser: None,
        variant: Variant,
        rated: bool,
        speed: Speed,
        timeControl: TimeControl,
        color: Literal["white", "black", "random"],
        perf: object,
        urlWhite: str,
        urlBlack: str,
        open: object,
        finalColor: GameColor | None = None,
        initialFen: str | None = None,
        **kwargs,
    ):
        self.id = id
        self.url = url
        self.status: ChallengeStatus = status
        self.challenger = challenger
        self.destUser = destUser
        self.variant = variant
        self.rated = rated
        self.speed: Speed = speed
        self.timeControl = timeControl
        self.color: Literal["white", "black", "random"] = color
        self.finalColor: GameColor | None = finalColor
        self.perf = perf
        self.initialFen = initialFen
        self.urlWhite = urlWhite
        self.urlBlack = urlBlack
        self.open = open
