from gemini_framework.abstract.unit_abstract import UnitAbstract


class GasBoilerUnit(UnitAbstract):
    """A GasBoilerUnit represents gas boiler modules."""

    def __init__(self, unit_id, unit_name, plant):
        super().__init__(unit_id=unit_id, unit_name=unit_name, plant=plant)
