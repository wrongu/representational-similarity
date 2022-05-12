import torch
from repsim.geometry.manifold import Manifold, Point, Scalar
from repsim.geometry.geodesic import point_along
from repsim.geometry.optimize import OptimResult
import warnings


def slerp(
    pt_a: Point,
    pt_b: Point,
    frac: float,
) -> Point:
    """
    Arc slerp between two points.

    https://en.m.wikipedia.org/wiki/Slerp

    The interpolated point will always have unit norm.

    Arguments:
        pt_a (Point): First point.
        pt_b (Point): Second point.
        frac (float): Fraction of the way from pt_a to pt_b.

    Returns:
        Point: The slerp between pt_a and pt_b.

    """
    assert 0.0 <= frac <= 1.0, "frac must be between 0 and 1"

    # Normalize a and b to unit vectors
    a = pt_a / torch.sqrt(torch.sum(pt_a * pt_a))
    b = pt_b / torch.sqrt(torch.sum(pt_b * pt_b))

    # Check cases where we can break early (and doing so avoids things like divide-by-zero later!)
    if frac == 0.0:
        return a
    elif frac == 1.0:
        return b
    elif torch.allclose(a, b):
        return (a + b) / 2

    # Get 'omega' - the angle between a and b
    ab = torch.sum(a*b)
    omega = torch.acos(torch.clip(ab, -1.0, 1.0))
    # Do interpolation using the SLERP formula
    a_frac = a * torch.sin((1 - frac) * omega) / torch.sin(omega)
    b_frac = b * torch.sin(frac * omega) / torch.sin(omega)
    return (a_frac + b_frac).reshape(a.shape)


def angle(pt_a: Point, pt_b: Point, pt_c: Point, space: Manifold, **kwargs) -> Scalar:
    """
    Angle B of triangle ABC, based on incident angle of geodesics AB and CB.
    If B is along the geodesic from A to C, then the angle is pi (180 degrees).
    If A=C, then the angle is zero.
    """
    pt_ba, converged_ba = point_along(pt_b, pt_a, space, frac=0.01, **kwargs)
    pt_bc, converged_bc = point_along(pt_b, pt_c, space, frac=0.01, **kwargs)
    if converged_ba != OptimResult.CONVERGED or converged_bc != OptimResult.CONVERGED:
        warnings.warn("point_along failed to converge; angle may be inaccurate")
    # Law of cosines using small local distances
    d_c, d_a, d_b = (
        space.length(pt_b, pt_ba),
        space.length(pt_b, pt_bc),
        space.length(pt_ba, pt_bc),
    )
    cos_b = 0.5 * (d_a * d_a + d_c * d_c - d_b * d_b) / (d_a * d_c)
    return torch.arccos(torch.clip(cos_b, -1.0, 1.0))


__all__ = ["angle"]
