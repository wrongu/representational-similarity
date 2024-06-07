import torch
from .kernel_base import Kernel
from .length_scale import auto_length_scale
from repsim.util import pdist2


class Radial(Kernel):
    def __init__(self, length_scale="auto"):
        super(Radial, self).__init__()
        self._scale = length_scale

    def set_scale(self, lengh_scale):
        self._scale = lengh_scale

    @property
    def _scale_str(self):
        if type(self._scale) is str:
            # Remove spaces
            return self._scale.replace(" ", "")
        else:
            return f"{self._scale:.3f}"

    def _rescale(self, x):
        if type(self._scale) == str:
            if x.shape[0] < x.shape[1]:
                raise RuntimeWarning(
                    "It's a bad idea to use automatic length-scale with too little data"
                )
            return x / auto_length_scale(x, self._scale)
        else:
            return x / self._scale


class SquaredExponential(Radial):
    def _call_impl(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        x, y = self._rescale(x), self._rescale(y)
        return torch.exp(-pdist2(x, y))

    def string_id(self):
        return f"SqExp[{self._scale_str}]"

    def effective_dim(self, x) -> float:
        return float("inf")


class Laplace(Radial):
    def _call_impl(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        x, y = self._rescale(x), self._rescale(y)
        return torch.exp(-torch.sqrt(pdist2(x, y)))

    def string_id(self):
        return f"Laplace[{self._scale_str}]"

    def effective_dim(self, x) -> float:
        return float("inf")
