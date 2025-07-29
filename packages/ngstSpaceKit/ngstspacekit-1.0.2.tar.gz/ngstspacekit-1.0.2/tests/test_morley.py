import ngsolve.meshes as ngm
import pytest
from ngsolve import GridFunction, Mesh, unit_square

import ngstSpaceKit


def test_morley_runs():
    mesh = Mesh(unit_square.GenerateMesh(maxh=0.25))

    morley = ngstSpaceKit.Morley(mesh)

    gfu = GridFunction(morley)
    assert len(gfu.vec) > 0


def test_morley_rejects_quads():
    mesh = ngm.MakeStructured2DMesh(nx=4, ny=4)

    with pytest.raises(ValueError):
        ngstSpaceKit.Morley(mesh)
