from ._internal import JsonDeserializable


class PlayTime(JsonDeserializable):
    """
    Play time

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/PlayTime.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, total: int, tv: int, **kwargs):
        self.total = total
        self.tv = tv
