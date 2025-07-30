from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np
from serde import serde, coerce

from seaice3p.params.dimensional.water import CubicLiquidus, LinearLiquidus

from .dimensional import (
    DimensionalParams,
    DimensionalEQMGasParams,
    DimensionalDISEQGasParams,
)


@serde(type_check=coerce)
@dataclass(frozen=True)
class BasePhysicalParams:
    """Not to be used directly but provides the common parameters for physical params
    objects
    """

    expansion_coefficient: float = 0.029
    concentration_ratio: float = 0.17
    stefan_number: float = 4.2
    lewis_salt: float = np.inf
    lewis_gas: float = np.inf
    frame_velocity: float = 0

    specific_heat_ratio: float = 0.5
    conductivity_ratio: float = 4.11
    eddy_diffusivity_ratio: float = 0
    snow_conductivity_ratio: float = 0.574

    # Option to change tolerable supersaturation
    tolerable_super_saturation_fraction: float = 1

    gas_viscosity_ratio: float = 0
    gas_bubble_eddy_diffusion: bool = False

    get_liquidus_temperature: Optional[Callable] = None
    get_liquidus_salinity: Optional[Callable] = None


@serde(type_check=coerce)
@dataclass(frozen=True)
class EQMPhysicalParams(BasePhysicalParams):
    """non dimensional numbers for the mushy layer"""


@serde(type_check=coerce)
@dataclass(frozen=True)
class DISEQPhysicalParams(BasePhysicalParams):
    """non dimensional numbers for the mushy layer"""

    # only used in DISEQ model
    damkohler_number: float = 1


PhysicalParams = EQMPhysicalParams | DISEQPhysicalParams


def get_dimensionless_physical_params(
    dimensional_params: DimensionalParams,
) -> PhysicalParams:

    if isinstance(dimensional_params.water_params.liquidus, LinearLiquidus):
        get_liquidus_salinity = None
        get_liquidus_temperature = None
    elif isinstance(dimensional_params.water_params.liquidus, CubicLiquidus):
        get_liquidus_salinity = (
            lambda T: dimensional_params.scales.convert_from_dimensional_bulk_salinity(
                dimensional_params.water_params.liquidus.get_liquidus_salinity(
                    dimensional_params.scales.convert_to_dimensional_temperature(T)
                )
            )
        )
        get_liquidus_temperature = (
            lambda S: dimensional_params.scales.convert_from_dimensional_temperature(
                dimensional_params.water_params.liquidus.get_liquidus_temperature(
                    dimensional_params.scales.convert_to_dimensional_bulk_salinity(S)
                )
            )
        )

    else:
        raise NotImplementedError

    """return a PhysicalParams object"""
    match dimensional_params.gas_params:
        case DimensionalEQMGasParams():
            return EQMPhysicalParams(
                expansion_coefficient=dimensional_params.expansion_coefficient,
                concentration_ratio=dimensional_params.water_params.concentration_ratio,
                stefan_number=dimensional_params.water_params.stefan_number,
                lewis_salt=dimensional_params.water_params.lewis_salt,
                lewis_gas=dimensional_params.lewis_gas,
                frame_velocity=dimensional_params.frame_velocity,
                specific_heat_ratio=dimensional_params.water_params.specific_heat_ratio,
                conductivity_ratio=dimensional_params.water_params.conductivity_ratio,
                eddy_diffusivity_ratio=dimensional_params.water_params.eddy_diffusivity_ratio,
                snow_conductivity_ratio=dimensional_params.water_params.snow_conductivity_ratio,
                tolerable_super_saturation_fraction=dimensional_params.gas_params.tolerable_super_saturation_fraction,
                gas_viscosity_ratio=dimensional_params.gas_params.gas_viscosity
                / dimensional_params.water_params.liquid_viscosity,
                gas_bubble_eddy_diffusion=dimensional_params.gas_params.gas_bubble_eddy_diffusion,
                get_liquidus_salinity=get_liquidus_salinity,
                get_liquidus_temperature=get_liquidus_temperature,
            )
        case DimensionalDISEQGasParams():
            return DISEQPhysicalParams(
                expansion_coefficient=dimensional_params.expansion_coefficient,
                concentration_ratio=dimensional_params.water_params.concentration_ratio,
                stefan_number=dimensional_params.water_params.stefan_number,
                lewis_salt=dimensional_params.water_params.lewis_salt,
                lewis_gas=dimensional_params.lewis_gas,
                frame_velocity=dimensional_params.frame_velocity,
                specific_heat_ratio=dimensional_params.water_params.specific_heat_ratio,
                conductivity_ratio=dimensional_params.water_params.conductivity_ratio,
                eddy_diffusivity_ratio=dimensional_params.water_params.eddy_diffusivity_ratio,
                snow_conductivity_ratio=dimensional_params.water_params.snow_conductivity_ratio,
                tolerable_super_saturation_fraction=dimensional_params.gas_params.tolerable_super_saturation_fraction,
                gas_viscosity_ratio=dimensional_params.gas_params.gas_viscosity
                / dimensional_params.water_params.liquid_viscosity,
                gas_bubble_eddy_diffusion=dimensional_params.gas_params.gas_bubble_eddy_diffusion,
                get_liquidus_salinity=get_liquidus_salinity,
                get_liquidus_temperature=get_liquidus_temperature,
                damkohler_number=dimensional_params.damkohler_number,
            )
        case _:
            raise NotImplementedError
