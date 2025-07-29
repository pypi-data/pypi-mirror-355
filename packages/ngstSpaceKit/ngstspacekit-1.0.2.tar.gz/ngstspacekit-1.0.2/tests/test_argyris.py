import ngsolve.meshes as ngm
import pytest
from ngsolve import GridFunction, Mesh, TaskManager, unit_square

import ngstSpaceKit
from tests.helper import calc_facet_gradient_jump, calc_facet_jump


def test_argyris_runs():
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    argyris = ngstSpaceKit.Argyris(mesh)

    gfu = GridFunction(argyris)
    assert len(gfu.vec) > 0


def test_argyris_rejects_quads():
    mesh = ngm.MakeStructured2DMesh(nx=4, ny=4)

    with pytest.raises(ValueError):
        ngstSpaceKit.Argyris(mesh)


@pytest.mark.parametrize("order", [5, 6, 7])
def test_argyris_is_continuous(order):
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))
    argyris = ngstSpaceKit.Argyris(mesh, order=order)
    gfu = GridFunction(argyris)

    for i in range(argyris.ndof):
        gfu.vec.data[:] = 0
        gfu.vec.data[i] = 100

        assert calc_facet_jump(gfu) == pytest.approx(0)


@pytest.mark.parametrize("order", [5, 6, 7])
def test_argyris_grad_is_continuous(order):
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))
    argyris = ngstSpaceKit.Argyris(mesh, order=order)
    gfu = GridFunction(argyris)

    for i in range(argyris.ndof):
        gfu.vec.data[:] = 0
        gfu.vec.data[i] = 100

        assert calc_facet_gradient_jump(gfu) == pytest.approx(0)
