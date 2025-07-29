from ._internal import JsonDeserializable


class Ok(JsonDeserializable):
    """
    Ok

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/Ok.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, ok: bool, **kwargs):
        self.ok = ok
