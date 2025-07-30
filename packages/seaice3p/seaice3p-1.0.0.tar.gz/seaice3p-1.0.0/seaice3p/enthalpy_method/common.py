from typing import Tuple
from numpy.typing import NDArray
import numpy as np
from scipy.optimize import fsolve
from ..state import State
from ..params import Config, PhysicalParams
from .phase_boundaries import get_phase_masks


def calculate_common_enthalpy_method_vars(
    state: State, cfg: Config, phase_masks
) -> Tuple[NDArray, NDArray, NDArray, NDArray]:
    physical_params = cfg.physical_params
    phase_masks = get_phase_masks(state, physical_params)
    solid_fraction = _calculate_solid_fraction(state, physical_params, phase_masks)
    liquid_fraction = _calculate_liquid_fraction(solid_fraction)
    temperature = _calculate_temperature(
        state, solid_fraction, physical_params, phase_masks
    )
    liquid_salinity = _calculate_liquid_salinity(
        state, temperature, phase_masks, physical_params
    )
    return solid_fraction, liquid_fraction, temperature, liquid_salinity


def _calculate_solid_fraction(state, physical_params: PhysicalParams, phase_masks):
    enthalpy, salt = state.enthalpy, state.salt

    # don't let salinity go below 1e-6
    conc = physical_params.concentration_ratio
    salt = np.where(salt + conc < 1e-6, -conc + 1e-6, salt)

    solid_fraction = np.full_like(enthalpy, np.nan)
    L, M, E, S = phase_masks
    St = physical_params.stefan_number
    ratio = physical_params.specific_heat_ratio

    solid_fraction[L] = 0
    solid_fraction[E] = -(1 + enthalpy[E]) / (St + ratio - 1)
    solid_fraction[S] = 1

    if np.all(M == False):
        return solid_fraction

    # Linear lqiuidus
    if physical_params.get_liquidus_salinity is None:
        A = St + conc * (1 - ratio)
        B = enthalpy[M] - St - conc + salt[M] * (1 - ratio)
        C = -(enthalpy[M] + salt[M])

        solid_fraction[M] = (1 / (2 * A)) * (-B - np.sqrt(B**2 - 4 * A * C))
        return solid_fraction

    # Cubic liquidus
    else:

        def residual(solid_fraction):
            temperature = (enthalpy[M] + solid_fraction * St) / (
                1 + (ratio - 1) * solid_fraction
            )
            return (
                salt[M]
                + (conc + physical_params.get_liquidus_salinity(temperature))
                * solid_fraction
                - physical_params.get_liquidus_salinity(temperature)
            )

        solid_fraction[M] = fsolve(residual, np.full_like(enthalpy[M], 0.5))

    return solid_fraction


def _calculate_temperature(
    state, solid_fraction, physical_params: PhysicalParams, phase_masks
):
    enthalpy = state.enthalpy
    L, M, E, S = phase_masks
    St = physical_params.stefan_number
    ratio = physical_params.specific_heat_ratio

    temperature = np.full_like(enthalpy, np.nan)
    temperature[L] = enthalpy[L]
    temperature[M] = (enthalpy[M] + solid_fraction[M] * St) / (
        1 + (ratio - 1) * solid_fraction[M]
    )
    temperature[E] = -1
    temperature[S] = (enthalpy[S] + St) / ratio

    return temperature


def _calculate_liquid_fraction(solid_fraction):
    return 1 - solid_fraction


def _calculate_liquid_salinity(state, temperature, phase_masks, physical_params):
    salt = state.salt

    # don't let salinity go below 1e-6
    conc = physical_params.concentration_ratio
    salt = np.where(salt + conc < 1e-6, -conc + 1e-6, salt)

    liquid_salinity = np.full_like(salt, np.nan)
    L, M, E, S = phase_masks

    liquid_salinity[L] = salt[L]
    liquid_salinity[M] = -temperature[M]
    liquid_salinity[E] = 1
    liquid_salinity[S] = 1

    return liquid_salinity
