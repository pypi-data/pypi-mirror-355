import ngsolve.meshes as ngm
import pytest
from ngsolve import GridFunction, Mesh, unit_cube, unit_square

import ngstSpaceKit
from tests.helper import calc_facet_jump


def test_hermite_runs():
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    hermite = ngstSpaceKit.Hermite(mesh)

    gfu = GridFunction(hermite)
    assert len(gfu.vec) > 0


def test_hermite_3d_runs():
    mesh = Mesh(unit_cube.GenerateMesh(maxh=0.25))

    hermite = ngstSpaceKit.Hermite(mesh)

    gfu = GridFunction(hermite)
    assert len(gfu.vec) > 0


def test_hermite_rejects_quads():
    mesh = ngm.MakeStructured2DMesh(nx=4, ny=4)

    with pytest.raises(ValueError):
        ngstSpaceKit.Hermite(mesh)


def test_hermite_is_continuous():
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))
    hermite = ngstSpaceKit.Hermite(mesh)
    gfu = GridFunction(hermite)

    for i in range(hermite.ndof):
        gfu.vec.data[:] = 0
        gfu.vec.data[i] = 1

        assert calc_facet_jump(gfu) == pytest.approx(0)
