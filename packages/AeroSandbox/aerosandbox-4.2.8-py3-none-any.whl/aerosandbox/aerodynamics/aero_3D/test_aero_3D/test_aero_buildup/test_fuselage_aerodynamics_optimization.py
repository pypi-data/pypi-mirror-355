import aerosandbox as asb
import aerosandbox.numpy as np
import pytest


def test_fuselage_aerodynamics_optimization():
    opti = asb.Opti()

    alpha = opti.variable(init_guess=0, lower_bound=0, upper_bound=30)
    beta = opti.variable(init_guess=0)

    fuselage = asb.Fuselage(
        xsecs=[
            asb.FuselageXSec(
                xyz_c=[xi, 0, 0],
                radius=asb.Airfoil("naca0010").local_thickness(0.8 * xi),
            )
            for xi in np.cosspace(0, 1, 20)
        ],
    )

    aero = asb.AeroBuildup(
        airplane=asb.Airplane(fuselages=[fuselage]),
        op_point=asb.OperatingPoint(velocity=10, alpha=alpha, beta=beta),
    ).run()

    opti.minimize(-aero["L"] / aero["D"])
    sol = opti.solve(verbose=True)
    print(sol(alpha))
    assert sol(alpha) > 10 and sol(alpha) < 20
    assert sol(beta) == pytest.approx(0, abs=1e-3)

    opti.minimize(aero["D"])
    sol = opti.solve(verbose=False)
    assert sol(alpha) == pytest.approx(0, abs=1e-2)
    assert sol(beta) == pytest.approx(0, abs=1e-2)


if __name__ == "__main__":
    test_fuselage_aerodynamics_optimization()
    pytest.main()
