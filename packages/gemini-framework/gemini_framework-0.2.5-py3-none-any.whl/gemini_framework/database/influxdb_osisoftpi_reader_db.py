from gemini_framework.abstract.database_reader_abstract import DatabaseReaderAbstract
from gemini_framework.database.connector.osisoftpi_driver import OsisoftPIDriver


class InfluxdbOsisoftPIReaderDB(DatabaseReaderAbstract):

    def __init__(self, category):
        super().__init__()
        self.category = category
        self.external_db_driver = OsisoftPIDriver()

    def set_external_db_parameters(self):
        self.parameters['osisoftpi']['interval'] = self.delta_t

        self.external_db_driver.update_parameters(self.parameters['osisoftpi'])
