import torch
from repsim.geometry.manifold import Manifold, Point, Scalar
from repsim.geometry.optimize import minimize, OptimResult
from typing import Union, Iterable, List, Tuple
import warnings


def path_length(pts: Iterable[Point],
                space: Manifold) -> Scalar:
    l, pt_a = Scalar([0.]), None
    for pt_b in pts:
        if pt_a is not None:
            l += space.length(pt_a, pt_b)
        pt_a = pt_b
    return l


def subdivide_geodesic(pt_a: Point,
                       pt_b: Point,
                       space: Manifold,
                       octaves: int = 5,
                       **kwargs) -> List[Point]:
    midpt, converged = midpoint(pt_a, pt_b, space , **kwargs)
    if not converged:
        warnings.warn(f"midpoint() failed to converge; remaining {octaves} subdivisions may be inaccurate")
    if octaves > 1 and converged:
        # Recursively subdivide each half
        left_half = subdivide_geodesic(pt_a, midpt, space, octaves-1)
        right_half = subdivide_geodesic(midpt, pt_b, space, octaves-1)
        return left_half + right_half[1:]
    else:
        # Base case
        return [pt_a, midpt, pt_b]


def point_along(pt_a: Point,
                pt_b: Point,
                space: Manifold,
                frac: float,
                guess: Union[Point, None] = None,
                **kwargs) -> Tuple[Point, OptimResult]:
    """Given ptA and ptB, return ptC along the geodesic between them, such that d(ptA,ptC) is frac percent of the
    total length ptA to ptB.
    """

    if frac < 0. or frac > 1.:
        raise ValueError(f"'frac' must be in [0, 1] but is {frac}")

    # Three cases where we can just break early without optimizing
    if frac == 0.:
        return pt_a, OptimResult.CONVERGED
    elif frac == 1.:
        return pt_b, OptimResult.CONVERGED
    elif torch.allclose(pt_a, pt_b, atol=kwargs.get('pt_tol', 1e-6)):
        return space.project((pt_a+pt_b)/2), OptimResult.CONVERGED

    # For reference, we know we're on the geodesic when dist_ap + dist_pb = dist_ab
    dist_ab = space.length(pt_a, pt_b)

    # Default initial guess to projection of euclidean interpolated point
    pt = space.project(guess) if guess is not None else space.project((1-frac)*pt_a + frac*pt_b)

    def calc_error(pt_c):
        # Two sources of error: total length should be dist_ab, and dist_a/(dist_a+dist_b) should equal 'frac'
        dist_a, dist_b = space.length(pt_a, pt_c), space.length(pt_c, pt_b)
        total_length = dist_a + dist_b
        length_error = torch.clip(total_length - dist_ab, 0., None)
        frac_error = torch.abs(dist_a - frac*dist_ab)
        return length_error + frac_error

    return minimize(calc_error, pt, space, **kwargs)


def midpoint(pt_a: Point,
             pt_b: Point,
             space: Manifold,
             **kwargs) -> Tuple[Point, OptimResult]:
    return point_along(pt_a, pt_b, space, frac=0.5, **kwargs)


__all__ = ["path_length", "subdivide_geodesic", "point_along", "midpoint"]
