from abc import ABC, abstractmethod
from gemini_framework.database.connector.influxdb_driver import InfluxdbDriver
import os
from datetime import datetime, timedelta, timezone
import pytz
import logging
import traceback

tz_ams = pytz.timezone('Europe/Amsterdam')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class DatabaseReaderAbstract(ABC):
    """Abstract class for Database Reader."""

    def __init__(self):
        self.category = None
        self.internal_db_driver = InfluxdbDriver()
        self.external_db_driver = None

        self.tags = []
        self.parameters = dict()
        self.delta_t = 900
        self.logger = logger

    def update_parameters(self, parameters):
        for key, value in parameters.items():
            self.parameters[key] = value

        self.delta_t = self.parameters[self.category]['interval']

        self.set_internal_db_parameters()
        self.set_external_db_parameters()

    def set_internal_db_parameters(self):
        influxdb_param = {
            "url": os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
            "org": os.getenv('INFLUXDB_ORG', 'TNO'),
            "username": os.getenv('INFLUXDB_USERNAME', 'gemini-user'),
            "password": os.getenv('INFLUXDB_PASSWORD', 'gemini-password'),
            "bucket": os.getenv('INFLUXDB_BUCKET', 'gemini-project'),
        }

        self.internal_db_driver.update_parameters(influxdb_param)

    @abstractmethod
    def set_external_db_parameters(self):
        pass

    def connect(self):
        self.internal_db_driver.connect()
        self.external_db_driver.connect()

    def disconnect(self):
        self.internal_db_driver.disconnect()
        self.external_db_driver.disconnect()

    def register_tags(self, units):
        for unit in units:
            for key, value in unit.tags[self.category].items():
                tag = {'plant_name': unit.plant.name,
                       'asset_name': unit.name,
                       'internal_tagname': key + '.' + self.category,
                       'external_tagname': value[-1]}

                self.tags.append(tag)

    def get_current_time_str(self):
        current_time_datetime = self.round_minutes(datetime.utcnow(), 'down', self.delta_t / 60)
        current_time_str = current_time_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

        return current_time_str

    def write_internal_database(self, plant_name, asset_name, internal_tagname, time, result):
        self.internal_db_driver.write_data(plant_name, asset_name,
                                           internal_tagname, time, result)

    def read_internal_database(self, plant_name, asset_name, internal_tagname, starttime_str,
                               endtime_str, timestep=None):
        if timestep is None:
            timestep = self.delta_t

        result, time = self.internal_db_driver.read_data(plant_name, asset_name,
                                                         internal_tagname, starttime_str,
                                                         endtime_str, timestep)

        return result, time

    def read_external_database(self, external_tagname, starttime_str, endtime_str, timestep=None):
        if timestep is None:
            timestep = self.delta_t

        result, time = self.external_db_driver.read_data(external_tagname,
                                                         starttime_str, endtime_str, timestep)

        return result, time

    def get_internal_database_last_time_str(self, plant_name, asset_name, tagname):
        _, timestamps = self.internal_db_driver.get_last_data(plant_name, asset_name, tagname)

        if timestamps:
            lasttime_str = timestamps[0]
        else:
            lasttime_datetime = datetime.strptime(self.parameters['start_time'],
                                                  '%Y-%m-%d %H:%M:%S')
            lasttime_datetime = tz_ams.localize(lasttime_datetime)
            lasttime_str = lasttime_datetime.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ")

        return lasttime_str

    def delete(self, plant_name):
        self.internal_db_driver.delete_database_all(plant_name)

    def import_raw_data(self):
        endtime_str = self.get_current_time_str()

        for tag in self.tags:
            if tag['external_tagname'] == '':
                continue

            starttime_str = self.get_internal_database_last_time_str(tag['plant_name'],
                                                                     tag['asset_name'],
                                                                     tag['internal_tagname'])

            if not (starttime_str == endtime_str):
                try:
                    self.logger.info('Reading ' + tag[
                        'external_tagname'] + ' from ' + starttime_str + ' to ' + endtime_str)

                    result, time = self.read_external_database(tag['external_tagname'],
                                                               starttime_str, endtime_str)

                    self.logger.info('Writing : ' + tag['internal_tagname'] + ' of ' + tag[
                        'asset_name'] + ' from ' + starttime_str + ' to ' + endtime_str)

                    self.write_internal_database(tag['plant_name'], tag['asset_name'],
                                                 tag['internal_tagname'], time, result)
                except Exception:
                    self.logger.error(
                        "ERROR in module " + self.__class__.__name__ + " : " +
                        traceback.format_exc())

    @staticmethod
    def round_minutes(dt, direction, resolution):
        new_minute = (dt.minute // resolution + (1 if direction == 'up' else 0)) * resolution

        return dt + timedelta(minutes=new_minute - dt.minute, seconds=-dt.second,
                              microseconds=-dt.microsecond)
