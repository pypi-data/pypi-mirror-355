from abc import ABC


class UnitAbstract(ABC):
    """Abstract class for Unit."""

    def __init__(self, unit_id, unit_name, plant):
        """Basic constructor for unit objects.

        :param str unit_id: The unique identifier of the unit.
        :param str unit_name: The name of the unit.
        :param object plant: The plant.
        """

        self.id = unit_id
        self.name = unit_name
        self.plant = plant
        self.parameters = {'timestamps': [], 'property': []}
        self.tags = {'timestamps': [], 'measured': {}, 'filtered': {}, 'calculated': {}}
        self.modules = {'preprocessor': [], 'model': [], 'postprocessor': []}
        self.from_units = []
        self.to_units = []

    def link(self):
        for phases in list(self.modules.keys()):
            module_list = self.modules[phases]

            for ii in range(0, len(module_list)):
                module_list[ii].link()

    def set_parameters(self, parameters):
        """function to set unit parameters.
        .
        :param dict parameters: dict of parameters property.
        """
        self.parameters['timestamps'] = parameters['timestamps']
        self.parameters['property'] = parameters['property']

    def set_tagnames(self, tagnames):
        """function to set unit parameters.
.
        :param dict tagnames: tagnames that need to be updated.
        """
        self.tags['timestamps'] = tagnames['timestamps']
        for category in ['measured', 'filtered', 'calculated']:
            for key, value in tagnames[category].items():
                self.tags[category][key] = value

    def update_model_parameter(self, timestamps):
        pass
