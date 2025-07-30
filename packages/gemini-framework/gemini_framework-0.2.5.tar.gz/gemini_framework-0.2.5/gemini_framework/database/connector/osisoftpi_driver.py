from gemini_framework.abstract.database_driver_abstract import DatabaseDriverAbstract
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse
import requests
import json


class OsisoftPIDriver(DatabaseDriverAbstract):
    """ database connector based on OSISOFTPI"""

    def __init__(self):
        """ Establish connection to OSISOFT database

        """
        self.parameters = dict()

    def update_parameters(self, parameters):
        for key, value in parameters.items():
            self.parameters[key] = value

    def connect(self):
        self.security_auth = HTTPBasicAuth(self.parameters['username'], self.parameters['password'])

    def disconnect(self):
        return

    def read_data(self, pi_af_tagname, start_time, end_time, interval):

        query_result = self._get_AF_interpolated_values(pi_af_tagname, start_time, end_time,
                                                        interval)

        results = []
        timestamps = []

        for record in query_result:
            results.append(record['Value'])
            timestamps.append(record['Timestamp'])

        return results, timestamps

    def write_data(self):
        return

    def _get_AF_interpolated_values(self, pi_af_tagname, start_time, end_time, interval):
        request_url = '{}/attributes?path=\\\\{}'.format(self.parameters['url'], pi_af_tagname)

        url = urlparse(request_url)

        response = requests.get(url.geturl(), auth=self.security_auth)
        if response.status_code == 200:
            #  Deserialize the JSON Response
            data = json.loads(response.text)

            url = urlparse(self.parameters['url'] + '/streams/' + data['WebId'] +
                           '/recorded?startTime=' + start_time + '&endtime=' + end_time +
                           '&interval=' + interval + 's')

            #  Read the set of values
            response = requests.get(url.geturl(), auth=self.security_auth)

            return json.loads(response.text)
        else:
            print(response.status_code, response.reason, response.text)

        return response.status_code
