from ._internal import JsonDeserializable


class CloudEval(JsonDeserializable):
    """
    CloudEval

    See https://github.com/lichess-org/api/blob/master/doc/specs/schemas/CloudEval.yaml
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None:
            return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, *, depth: int, fen: str, nodes: int, pvs: tuple[object, ...], **kwargs):
        self.depth = depth
        self.fen = fen
        self.nodes = nodes
        self.pvs = pvs
