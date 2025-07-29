import pytest
from ngsolve import (
    BND,
    VOL,
    GridFunction,
    Integrate,
    Mesh,
    dx,
    unit_square,
)

import ngstSpaceKit.bubbles


@pytest.mark.parametrize("order", range(-5, 2))
def test_edge_bubble_rejects_low_order(order):
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    with pytest.raises(ValueError):
        _ = ngstSpaceKit.bubbles.EdgeBubble(mesh, order)


@pytest.mark.parametrize("order", range(2, 6))
def test_edge_bubble_is_zero_at_vertices(order):
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    bubbles = ngstSpaceKit.bubbles.EdgeBubble(mesh, order)

    gfu = GridFunction(bubbles)
    gfu.vec.data[:] = 100.0

    assert (
        Integrate(
            gfu**2 * dx(element_vb=VOL, bonus_intorder=order), gfu.space.mesh
        )
        > 1.0
    )
    assert (
        Integrate(
            gfu**2 * dx(element_vb=BND, bonus_intorder=order), gfu.space.mesh
        )
        > 1.0
    )

    # Integrate() does not work on BBND,
    # so we test each point individually
    for vertex in mesh.vertices:
        point = vertex.point
        assert pytest.approx(gfu(x=point[0], y=point[1])) == 0.0


@pytest.mark.parametrize("order", range(-5, 3))
def test_volume_bubble_rejects_low_order(order):
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    with pytest.raises(ValueError):
        _ = ngstSpaceKit.bubbles.VolumeBubble(mesh, order)


@pytest.mark.parametrize("order", range(3, 6))
def test_volume_bubble_has_zero_trace(order):
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    bubbles = ngstSpaceKit.bubbles.VolumeBubble(mesh, order)

    gfu = GridFunction(bubbles)
    gfu.vec.data[:] = 100.0

    assert (
        Integrate(
            gfu**2 * dx(element_vb=VOL, bonus_intorder=order), gfu.space.mesh
        )
        > 1.0
    )

    assert (
        Integrate(
            gfu**2 * dx(element_vb=BND, bonus_intorder=order), gfu.space.mesh
        )
        < 1e-13
    )
