from ._internal import JsonDeserializable


class Clock(JsonDeserializable):
    """
    Clock

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/Clock.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, limit: int, increment: int, **kwargs):
        self.limit = limit
        self.increment = increment
