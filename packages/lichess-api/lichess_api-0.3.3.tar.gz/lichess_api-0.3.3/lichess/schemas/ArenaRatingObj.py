from ._internal import JsonDeserializable

from .PerfType import PerfType


class ArenaRatingObj(JsonDeserializable):
    """
    ArenaRatingObj

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/ArenaRatingObj.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, *, rating: int, perf: PerfType | None = None, **kwargs):
        self.perf: PerfType | None = perf
        self.rating = rating
