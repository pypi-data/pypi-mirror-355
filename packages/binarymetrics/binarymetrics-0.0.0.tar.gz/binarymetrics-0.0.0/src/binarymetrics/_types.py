from safecheck import Bool, Float, Integer, NumpyArray, TorchArray


class TFloat:
    """Typing helper for a PyTorch floating tensor."""

    def __class_getitem__(cls, shape: str):
        return Float[TorchArray, shape]

class TInt:
    """Typing helper for a PyTorch integer tensor."""

    def __class_getitem__(cls, shape: str):
        return Integer[TorchArray, shape]

class TBool:
    """Typing helper for a PyTorch boolean tensor."""

    def __class_getitem__(cls, shape: str):
        return Bool[TorchArray, shape]

class NFloat:
    """Typing helper for a NumPy floating array."""

    def __class_getitem__(cls, shape: str):
        return Float[NumpyArray, shape]

class NInt:
    """Typing helper for a NumPy integer array."""

    def __class_getitem__(cls, shape: str):
        return Integer[NumpyArray, shape]

class NBool:
    """Typing helper for a NumPy boolean array."""

    def __class_getitem__(cls, shape: str):
        return Bool[NumpyArray, shape]
