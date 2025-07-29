from ngsolve import CF, CoefficientFunction, GridFunction, Trace, grad


def hesse(f: CoefficientFunction) -> CoefficientFunction:
    """
    Hesse matrix of a function.
    """
    return f.Operator("hesse")


def laplace(f: GridFunction) -> CoefficientFunction:
    """
    Laplace operator on a function that is scalar or vector valued.
    """
    f_hesse = hesse(f)
    dim = f.space.mesh.dim
    if len(f.shape) == 0:
        # f is scalar valued
        return Trace(f_hesse)
    elif len(f.shape) == 1:
        # f is vector valued
        return CF(
            tuple(
                # f_hesse[j,:] == f[j].Operator("hesse")
                # it would be nicer to sum over all diagonal indices f_hesse[j, i, i] for i in range (dim),
                # but ngsolve ravels dim. 2 and 3 into one dimension, so
                # (i,i) -> i*dim + i
                sum(f_hesse[j, i] for i in range(0, dim * dim, dim + 1))
                for j in range(dim)
            )
        )
    else:
        raise ValueError("The function f is not scalar or vector valued.")


def del_x(f: CoefficientFunction) -> CoefficientFunction:
    """
    partial derivative in first coordinate direction
    """
    return grad(f)[0]


def del_y(f: CoefficientFunction) -> CoefficientFunction:
    """
    partial derivative in second coordinate direction
    """
    return grad(f)[1]


def del_z(f: CoefficientFunction) -> CoefficientFunction:
    """
    partial derivative in third coordinate direction
    """
    return grad(f)[2]


def del_xx(f: CoefficientFunction) -> CoefficientFunction:
    """
    partial derivative of second order, in first and first coordinate direction
    """
    return hesse(f)[0, 0]


def del_xy(f: CoefficientFunction) -> CoefficientFunction:
    """
    partial derivative of second order, in first and second coordinate direction
    """
    return hesse(f)[0, 1]


def del_yy(f: CoefficientFunction) -> CoefficientFunction:
    """
    partial derivative of second order, in second and second coordinate direction
    """
    return hesse(f)[1, 1]
