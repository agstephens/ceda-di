"""
Interface for reading data from ENVI BSQ/BIL packed binary files.
Also contains methods for extracting metadata (geospatial/temporal).
"""

import logging
import json
import os


from ceda_di.filetypes.file_io import envi_io
from ceda_di.providers import arsf
from ceda_di.metadata import product
from ceda_di._dataset import _geospatial


class ENVI(_geospatial):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.logger = logging.getLogger(__name__)
        self.b = None  # Overridden by child classes
        self.data = None  # Overridden by child classes
        self.data_format = None  # Overridden by child classes
        self.extension = None  # Overridden by child classes
        self.parameters = None  # Overridden by child classes
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def _load_data(self):
        """
        Load data from the binary file into a class attribute "data"
        """
        if self.data is None:
            self.parameters = self.b.hdr
            self.data = self.b.read()

    def get_parameters(self):
        """
        Return a list of Parameter objects containing parameter information.

        :return: A list of Parameter objects containing parameter information.
        """
        params = []
        for p_name in self.parameters:
            params.append(product.Parameter(p_name))

        return params

    def get_geospatial(self):
        """
        Read geospatial data parsed from binary file

        :returns: A dict containing geospatial information
        """
        spatial = {
            "type": "track",
            "lat": self.data[1],
            "lon": self.data[2],
            "alt": self.data[3],
            "roll": self.data[4],
            "pitch": self.data[5],
            "heading": self.data[6]
        }

        return spatial

    def get_temporal(self):
        """
        Return a dictionary containing the start and end times of the data file.

        :returns: A dict containing temporal data.
        """
        temporal = {
            "start_time": self.data[0][0],
            "end_time": self.data[0][-1],
        }

        return temporal

    def get_data_format(self):
        """
        Return file format information

        :returns: A dict containing file format information
        """
        data_format = {
            "format": self.data_format,
        }

        return data_format

    def get_properties(self):
        """
        Return a metadata.product.Properties object describing
        the file's metadata.

        :returns: Metadata.product.Properties object describing the file.
        """
        filesystem = super(ENVI, self).get_filesystem(self.path)

        self._load_data()
        if "band names" in self.parameters:
            self.parameters = self.parameters["band names"]

        instrument = arsf.Hyperspectral.get_instrument(filesystem["filename"])
        flight_info = arsf.Hyperspectral.get_flight_info(filesystem["filename"])
        prop = product.Properties(filesystem=filesystem,
                                  temporal=self.get_temporal(),
                                  data_format=self.get_data_format(),
                                  spatial=self.get_geospatial(),
                                  parameters=self.get_parameters(),
                                  instrument=instrument,
                                  flight_info=flight_info)
        return prop


class BIL(ENVI):
    """
    Sub-class of ENVI that uses the envi_io.BilFile class to read
    binary data from BIL files.
    """
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        super(BIL, self).__init__(header_path, path, unpack_fmt)
        self.extension = ".bil"
        self.data_format = "ENVI BIL (Band Interleaved by Line)"

        # Construct file access object
        self.b = envi_io.BilFile(header_path=self.header_path,
                                 path=self.path,
                                 unpack_fmt=self.unpack_fmt)
        self.path = self.b.path

    def __enter__(self):
        self.read()
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        """
        Return a dict containing a summary of the file's data.

        :returns: A dict containing a summary of the file's data.
        """
        self._load_data()
        return self.data


class BSQ(ENVI):
    """
    Sub-class of ENVI that uses the envi_io.BsqFile class to read
    binary data from BSQ files.
    """
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        super(BSQ, self).__init__(header_path, path, unpack_fmt)
        self.extension = ".bsq"
        self.data_format = "ENVI BSQ (Band Sequential)"

        # Construct file access object
        self.b = envi_io.BsqFile(header_path=self.header_path,
                                 path=self.path,
                                 unpack_fmt=self.unpack_fmt)
        self.path = self.b.path

    def __enter__(self):
        self.data = self.read()
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        """
        Return a dict containing a summary of the file's data.

        :returns: A dict containing a summary of the file's data.
        """
        self._load_data()
        return self.data

#kltsa 6/6/2016 issue 23254 : simple handler for extracting metadata from 
#                             .hdr files.
class HDRFile:

    def __init__(self, path):
        self.hdrvars = {}
        self.path = path
        with open(self.path) as hdrfile:
            for line in hdrfile:
                name, var = line.partition("=")[::2]
                self.hdrvars[name.strip()] = var
    def get_properties(self):

        path = os.path.dirname(self.path)
        size = round(os.path.getsize(self.path) / (1024*1024.0), 3)
        filename = os.path.basename(self.path)
        coordinates_styring = self.hdrvars["map info"].split(",")
        lon = []
        lon.append(coordinates_styring[2])
        lon.append(coordinates_styring[4])
        lon.append(coordinates_styring[6])
        lat = []
        lat.append(coordinates_styring[1])
        lat.append(coordinates_styring[3])
        lat.append(coordinates_styring[5])

        coordinates = [[min(lon), min(lat)], [max(lon), max(lat)]]

        request = {\
                   "data_format": {"format": "hdr"},\
                   "file":\
                   {\
                    "symlinks": [],\
                    "path": path,\
                    "size": size,\
                    "filename": filename\
                   },\
                   "spatial":\
                   {\
                    "geometries":\
                    {\
                     "search":\
                     {"type": "envelope",\
                      "coordinates": coordinates\
                     }\
                    }\
                   }\
                  }

        return json.dumps(request)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
