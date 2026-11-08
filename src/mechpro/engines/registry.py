from mechpro.calculations.registry import CalculationEngineRegistry
from mechpro.engines.gas.demand import GasApplianceDemandEngine


def create_default_calculation_engine_registry() -> CalculationEngineRegistry:
    """Build the supported calculation-engine registry for the desktop application."""
    registry = CalculationEngineRegistry()
    registry.register(GasApplianceDemandEngine())
    return registry
