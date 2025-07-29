from typing import Optional

from ngsolve import (
    BND,
    COUPLING_TYPE,
    L2,
    CoefficientFunction,
    InnerProduct,
    Mesh,
    NormalFacetFESpace,
    VectorL2,
    div,
    dx,
    grad,
    specialcf,
)
from ngstrefftz import (
    CompoundEmbTrefftzFESpace,
    EmbeddedTrefftzFES,
    TrefftzEmbedding,
)

from ngstSpaceKit.diffops import laplace


def WeakStokes(
    mesh: Mesh,
    order: int,
    normal_continuity: Optional[int] = None,
    rhs: Optional[CoefficientFunction] = None,
    nu: float = 1.0,
    dirichlet: str = "",
) -> CompoundEmbTrefftzFESpace:
    r"""
    The weak Stokes space
    - is tailored to be used to solve the Stokes equation
    - is normal continuous up to degree `normal_continuity` in the velocity part
    - has the remaining dofs adhering to the embedded Trefftz condition

    `normal_continuity`: If `None`, it is set to `order-1`.

    # Conforming Trefftz Formulation
    - $\mathbb{V}_h := [\mathbb{P}^{k, \text{disc}}(\mathcal{T}_h)]^d \times \mathbb{P}^{k-1, \text{disc}}(\mathcal{T}_h)$
    - $\mathbb{Q}_h := [\mathbb{P}^{k-2, \text{disc}}(\mathcal{T}_h)]^d \times \mathbb{P}^{k-1, \text{disc}}_0(\mathcal{T}_h)$
    - $\mathbb{Z}_h := [\mathbb{P}^{k_n}(\mathcal{F}_h)]^d, k_n \leq k$
    - \begin{align}
      \mathcal{C}_K(v_h, z_h) &:=
          \int_{\partial K} v_h^v \cdot n \; z_h \cdot n \;dx \\\\
      \mathcal{D}_K(y_h, z_h) &:=
          \int_{\partial K} y_h^v \cdot n \; z_h \cdot n \;dx
      \end{align}
    - \begin{align}
      (\mathcal{L}_K v_h, q_h) :=
        -\nu \int_\Omega \Delta v_h^v \cdot q_h^v \;dx + \int_\Omega \nabla v_h^p \cdot q_h^v + \mathrm{div}(v_h^v) q_h^p \;dx
      \end{align}
    """
    if order < 2:
        raise ValueError("requires order>=2")

    fes = VectorL2(mesh, order=order, dgjumps=True) * L2(
        mesh, order=order - 1, dgjumps=True
    )

    Q_test = L2(mesh, order=order - 1, dgjumps=True)
    for i in range(0, Q_test.ndof, Q_test.ndof // mesh.ne):
        Q_test.SetCouplingType(i, COUPLING_TYPE.UNUSED_DOF)

    fes_test = VectorL2(mesh, order=order - 2, dgjumps=True) * Q_test

    (u, p) = fes.TrialFunction()
    (v, q) = fes_test.TestFunction()

    top = (
        -nu * InnerProduct(laplace(u), v) * dx
        + InnerProduct(grad(p), v) * dx
        + div(u) * q * dx
    )
    trhs = rhs * v * dx(bonus_intorder=10) if rhs else None

    conformity_space = NormalFacetFESpace(
        mesh,
        order=normal_continuity if normal_continuity is not None else order - 1,
        dirichlet=dirichlet,
    )

    uc, vc = conformity_space.TnT()

    n = specialcf.normal(mesh.dim)

    cop_l = u * n * vc * n * dx(element_vb=BND)
    cop_r = uc * n * vc * n * dx(element_vb=BND)

    emb = TrefftzEmbedding(top=top, trhs=trhs, cop=cop_l, crhs=cop_r)
    weak_stokes = EmbeddedTrefftzFES(emb)
    assert type(weak_stokes) is CompoundEmbTrefftzFESpace, (
        "The weak Stokes space should always be an CompoundEmbTrefftzFESpace"
    )

    return weak_stokes
