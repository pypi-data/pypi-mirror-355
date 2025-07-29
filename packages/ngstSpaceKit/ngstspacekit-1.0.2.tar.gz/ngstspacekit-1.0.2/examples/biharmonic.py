# %%
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from netgen.occ import Circle, OCCGeometry, Rectangle, X, Y, gp_Pnt2d
from ngsolve import (
    BilinearForm,
    CoefficientFunction,
    GridFunction,
    Integrate,
    LinearForm,
    Mesh,
    TaskManager,
    ds,
    dx,
    grad,
    specialcf,
    sqrt,
    x,
    y,
)
from ngsolve.webgui import Draw

from ngstSpaceKit import Argyris
from ngstSpaceKit.argyris import ArgyrisDirichlet
from ngstSpaceKit.diffops import laplace

# %%
nu = -0.25

maxh = 1.0
R = 5


def mesh_circle(maxh: float = 0.25, R: float | int = 5) -> Mesh:
    order = 5
    circ = Circle(gp_Pnt2d(0, 0), R).Face()
    circ.edges.name = "circ"
    mesh = Mesh(OCCGeometry(circ, dim=2).GenerateMesh(maxh=maxh)).Curve(order)
    return mesh


def mesh_square(maxh: float = 0.25, R: float | int = 5) -> Mesh:
    square = Rectangle(R, R).Face()
    square.edges.name = "boundary"
    square.edges.Max(X).name = "right"
    square.edges.Min(X).name = "left"
    square.edges.Min(Y).name = "bottom"
    square.edges.Max(Y).name = "top"
    return Mesh(OCCGeometry(square, dim=2).GenerateMesh(maxh=maxh))


# %% [markdown]
# # The biharmonic equation
#
# The biharmonic equation with clamp boundary conditions reads as
# \begin{align}
# \Delta^2 u &= q \text{ in } \Omega, \\
# u &= 0 \text{ on } \partial \Omega, \\
# \nabla u \cdot n &= 0 \text{ on } \partial \Omega.
# \end{align}
# This equation describes the behavoiur of a plate bending under a load force of magnitude $q$.
#
# We arrive at the weak formulation: Find $u_h \in V_h$ s.t. for all $v_h \in V_h$ there holds
# \begin{align}
# \int_\Omega \Delta u_h \Delta v_h \,\mathrm{d} x= \int_\Omega q v_h \,\mathrm{d} x
# \end{align}
#
# For the formulation to make sense, we require $V_h \subseteq H^2(\Omega)$. One example of a $H^2$-conforming element is the Argyris element.


# %%
mesh = mesh_square(maxh, R)

dir_bnd = "left|right|top|bottom"
dir_lr = "left|right"
dir_tb = "top|bottom"

fes = Argyris(
    mesh,
    order=5,
    dirichlet=ArgyrisDirichlet(
        vertex_value=dir_bnd,
        deriv_x=dir_tb,
        deriv_y=dir_lr,
        deriv_xx=dir_tb,
        deriv_yy=dir_lr,
        deriv_normal_moment=dir_bnd,
    ),
)
u, v = fes.TnT()

a = BilinearForm(fes)

a += laplace(u) * laplace(v) * dx

a.Assemble()

f = LinearForm(fes)
f += v * dx
f.Assemble()

gfu = GridFunction(fes)

gfu.vec.data = a.mat.Inverse(freedofs=fes.FreeDofs()) * f.vec

# %%
Draw(gfu, deformation=True, euler_angles=[-60, 5, 30], order=5)

# %% [markdown]
# Let us consider another domain, that does not align with the $x$ or $y$ axes:
# a disc of radius $R$ centered at the origin. There exists an exact solution for this geometry.
#
# [\[Timoshenko, Woinowsky-Krieger, Eq. (62)\]](https://archive.org/embed/TheoryOfPlatesAndShells)
#
# Let $q := 1$ represent the constant load on the plate, let $D := 1$ represent the flexural rigidity of the plate.
#
# Then, the exact solution is given in polar coordinates by
# \begin{align}
# u(r, \phi) &= \frac{q}{64 D} \left(R^2 - r^2\right)^2.
# \end{align}

# %%
mesh = mesh_circle(maxh=maxh, R=R)
Draw(mesh)


# %%
def exact_solution(R=R):
    r = sqrt(x**2 + y**2)
    q = 1.0
    D = 1.0

    w_ex = (q) / (64 * D) * (R**2 - r**2) ** 2
    return w_ex


w_ex = exact_solution()

# %%
Draw(w_ex, mesh, deformation=True, euler_angles=[-60, 5, 30])


# %%
def biharmonic_solution(
    mesh: Mesh, lamda: float, rho: float, dirichlet: ArgyrisDirichlet
) -> GridFunction:
    """
    Solves the biharmonic equation with (weakly enforced) clamp boundary conditions.

    The clamp boundary conditions are enforced via the penalty method.
    `lamda`: penalty method parameter
    `rho`: penalty method parameter
    """
    # also Morley?
    fes = Argyris(mesh, order=5, dirichlet=dirichlet)
    u, v = fes.TnT()

    a = BilinearForm(fes)

    a += laplace(u) * laplace(v) * dx

    n = specialcf.normal(2)
    h = specialcf.mesh_size

    # penalty method
    a += lamda * h ** (-rho) * u * v * ds(skeleton=True)
    a += lamda * h ** (-rho) * (grad(u) * n) * (grad(v) * n) * ds(skeleton=True)

    a.Assemble()

    f = LinearForm(fes)
    f += v * dx
    f.Assemble()

    gfu = GridFunction(fes)

    gfu.vec.data = a.mat.Inverse(freedofs=fes.FreeDofs()) * f.vec
    return gfu


dirichlet = ArgyrisDirichlet(
    vertex_value="circ",
    deriv_x="circ",
    deriv_y="circ",
    deriv_normal_moment="circ",
)

# %% [markdown]
# Due to the domain not being aligned with the coordinate axes, we have a problem:

# %%
Draw(
    biharmonic_solution(mesh, 0.0, 1.0, dirichlet),
    mesh,
    deformation=True,
    euler_angles=[-60, 5, 30],
    order=5,
)

# %% [markdown]
# Problem: $u_h$ does not conform to the clamp conditions
#
# \begin{align}
# u_h &= g_D &&:= 0 \text{ on } \partial \Omega, \\
# \nabla u_h \cdot n &= g_{n,D} &&:= 0 \text{ on } \partial \Omega.
# \end{align}
#
# Fix: we add a penalty method
#
# \begin{align}
# \lambda_1 h^{-\rho_1} \int_{\partial \Omega} (u_h - g_D) v_h \,\mathrm{d} x +
# \lambda_2 h^{-\rho_2} \int_{\partial \Omega} ((\nabla u_h \cdot n) - g_{n,D}) \nabla v_h \cdot n \,\mathrm{d} x
# \end{align}
# to the equation $a_h(u_h, v_h) = f_h(v_h)$, where $h$ represents the local element diameter, $\lambda, \rho \geq 0$.
# This results in a bilinear form
#
# \begin{align}
# \tilde{a}_h(u_h, v_u) = \int_\Omega \Delta u_h \Delta v_h \,\mathrm{d} x +
# \lambda_1 h^{-\rho_1} \int_{\partial \Omega} u_h v_h \,\mathrm{d} x +
# \lambda_2 h^{-\rho_2} \int_{\partial \Omega} \nabla u_h \cdot n \ \nabla v_h \cdot n \,\mathrm{d} x.
# \end{align}


# %%
gfu = biharmonic_solution(mesh, 1e4, 2, dirichlet)

# %%
Draw(gfu, deformation=True, euler_angles=[-60, 5, 30], order=5)

# %%
Draw(w_ex - gfu, mesh, deformation=True, euler_angles=[-60, 5, 30], order=5)


# %%
def l2_err(a: CoefficientFunction, b: CoefficientFunction, mesh: Mesh):
    return sqrt(Integrate((a - b) ** 2, mesh))


def biharmoic_scaling(
    exact_solution: CoefficientFunction,
    lamda: float,
    rho: float,
    refinements: int = 6,
) -> Tuple[np.ndarray, np.ndarray]:
    errs = np.zeros(refinements)
    hs = np.zeros(refinements)
    for i in range(1, refinements + 1):
        with TaskManager():
            maxh = 0.5 * R / (2**i)
            mesh = mesh_circle(maxh=maxh, R=R)
            hs[i - 1] = maxh
            errs[i - 1] = l2_err(
                biharmonic_solution(mesh, lamda, rho, dirichlet),
                exact_solution,
                mesh,
            )
    return hs, errs


hs, errs = biharmoic_scaling(w_ex, 1e4, 2, 4)
_, errs_no_penalty = biharmoic_scaling(w_ex, 0, 2, 4)

# %%

b = 1e-0
a = 3
plt.loglog(
    hs,
    b * hs**a,
    label="$y \\in \\mathcal{O}" + f"(h^{a})" + "$",
    c="gray",
    linestyle="dotted",
)
plt.loglog(hs, errs, label="with penalty", marker="4")
plt.loglog(hs, errs_no_penalty, label="no penalty", marker="4")
plt.legend()
plt.xlabel("h")
plt.ylabel("$L^2$-error")
plt.show()
