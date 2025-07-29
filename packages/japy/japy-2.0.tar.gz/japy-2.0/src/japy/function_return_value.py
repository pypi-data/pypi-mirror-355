def is_json_serializable(obj):
    if isinstance(obj, (str, int, float, bool, type(None), list, dict)):
        return True
    return False


def is_tuple(obj):
    return isinstance(obj, tuple)


def to_serializable(obj):
    if is_json_serializable(obj):
        return obj
    elif is_tuple(obj):
        res = []
        for inner in obj:
            res.append(to_serializable(inner))
        return tuple(res)
    else:
        obj_dict = obj.__dict__
        for key in obj_dict.keys():
            obj_dict[key] = to_serializable(obj_dict[key])
        return obj_dict


class FunctionReturnValue:

    def __init__(self, value=None):
        self.class_name = type(value).__name__
        self.return_value = to_serializable(value)

    def to_dict(self):
        return {
            "returnValue": self.return_value,
            "className": self.class_name
        }
