from gemini_framework.abstract.database_reader_abstract import DatabaseReaderAbstract
from gemini_framework.database.connector.avevadb_driver import AvevaDriver


class InfluxdbAvevaReaderDB(DatabaseReaderAbstract):

    def __init__(self, category):
        super().__init__()

        self.category = category
        self.external_db_driver = AvevaDriver()

    def set_external_db_parameters(self):
        self.parameters['avevadb']['interval'] = self.delta_t

        self.external_db_driver.update_parameters(self.parameters['avevadb'])
