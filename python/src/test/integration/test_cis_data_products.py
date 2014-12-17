from unittest import TestCase
import json
import datetime as dt

from hamcrest import *

from ceda_di.extract import Extract
from di import read_conf
from jasmin_cis.test.test_files.data import *
from test.utils_for_testing.within_delta import within_delta
from test.utils_for_testing.corner_same_as_bounds import corner_in_bounds_by_delta
from test.integration.test_files.data import ceda_di_test_files


class CISProductTests(object):
    """
    Abstract class for testing products
    """

    CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../../../config/ceda_di.json')
    TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_files')

    @classmethod
    def setUpForTest(cls, product_name):
        # Process the file in the class setup method so it only has to do the slow bit once for all tests.
        config = read_conf(cls.CONFIG_FILE)
        config['output-path'] = cls.TEST_DIR
        config['json-path'] = cls.TEST_DIR + '/json'
        config['send-to-index'] = False
        config['no-create-files'] = False
        extract = Extract(config)
        cls.cis_test_file = cis_test_files[product_name]
        extract.process_file(cls.cis_test_file.master_filename)

    def get_output_json(self):
        fname = os.path.basename(self.cis_test_file.master_filename)
        json_path = os.path.join(self.TEST_DIR, 'json')
        out_fname = "%s/%s.json" % (json_path, os.path.splitext(fname)[0])

        fp = open(out_fname)
        return json.load(fp)

    def test_json_has_start_time(self):
        json_body = self.get_output_json()
        start_date_str = json_body['temporal']['start_time']
        start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S.%f")
        assert_that(start_date, is_(within_delta(self.cis_test_file.start_datetime, dt.timedelta(seconds=1))))

    def test_json_has_end_time(self):
        json_body = self.get_output_json()
        end_date_str = json_body['temporal']['end_time']
        end_date = dt.datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S.%f")
        assert_that(end_date, is_(within_delta(self.cis_test_file.end_datetime, dt.timedelta(seconds=1))))

    def test_json_has_geo_bounds(self):
        json_body = self.get_output_json()
        geo_bbox = json_body['spatial']['geometries']['bbox']
        coordinates = geo_bbox['coordinates']
        assert_that(coordinates, corner_in_bounds_by_delta(self.cis_test_file, 0.01))

    def test_json_has_parameters(self):
        json_body = self.get_output_json()
        parameters = json_body['parameters']
        assert_that(len(parameters), is_(self.cis_test_file.valid_vars_count))


        def get_variable_attribute_value_by_name(variable_attributes, attribute_name):
            """
            Get the value of a specified variable attribute from a list of attribute dictionaries,
            each containing a 'name' and 'value' key.
            :param variable_attributes: List of variable attribute dictionaries of format
            {"name": name, "value": value}
            :return: value of matching attribute
            """
            for attribute in variable_attributes:
                if attribute['name'] == attribute_name:
                    return attribute['value']

        for variable_attrs in parameters:
            name = get_variable_attribute_value_by_name(variable_attrs, 'standard_name')

            if name == self.cis_test_file.data_variable_name:
                for key, expected_value in self.cis_test_file.data_variable_properties.iteritems():
                    value = get_variable_attribute_value_by_name(variable_attrs, key)
                    assert_that(value, is_(str(expected_value)), "Value is present and matched for key '{}'".format(key))
                return

        # If we got here it means that we couldn't find a matching parameter so we should fail
        raise AssertionError("%s not found in list of parameters" % self.cis_test_file.data_variable_name)

    def test_json_has_correct_format_and_source(self):
        json_body = self.get_output_json()
        dataformat = json_body['data_format']['format']
        indexer = json_body['index_entry_creation']['indexer']
        assert_that(dataformat, is_(self.cis_test_file.file_format), "data format")
        assert_that(indexer, contains_string(self.cis_test_file.product_name), "data format")


class TestGASSP(CISProductTests, TestCase):
    """
    Test that CEDA DI can read GASSP data:
    """

    @classmethod
    def setUpClass(cls):
        cls.setUpForTest("GASSP_aeroplane")

class TestCloudSat(CISProductTests, TestCase):
    """
    Test that CEDA DI can read GASSP data:
    """

    @classmethod
    def setUpClass(cls):
        for key, value in ceda_di_test_files.iteritems():
            cis_test_files[key] = value
        cls.setUpForTest("cloudsat_PRECIP_2007")