import pandas as pd
import numpy as np


def get_data(path, type, no_transforms=False):
    """
    Converts data loaded from path into a new Data object. Also applies some base
    transformations unless no_transforms is set to True.
    """
    return Data(path, type).prepare(no_transforms)


class Data(object):
    """An object wrapping all base data operations.

    Attributes:
    data  pandas.DataFrame     the actual data loaded from the file
    hosts pandas.DataFrame     the extracted column with source addresses
    path  string/pathlib.Path  the path the data was originally loaded from
    type  string               filetype of the file, must be a key of Data.READERS

    Static:
    COLUMNS list has the required column names and possible aliases
    READERS dict mapping of filetypes to respective loading functions
    """
    COLUMNS = [
        ['proto', 'protocol'],
        ['dport', 'destinationport', 'dstport'],
        ['sport', 'sourceport', 'srcport'],
        ['state', 'st'],
        ['dur', 'duration'],
        ['totbytes', 'totalbytes', 'tbytes'],
        ['srcbytes', 'sourcebytes']
    ]
    READERS = {
        'csv': pd.read_csv,
        'feather': pd.read_feather,
        'fwf': pd.read_fwf,
        'stata': pd.read_stata,
        'json': pd.read_json,
        'pickle': pd.read_pickle,
        'parquet': pd.read_parquet,
        'excel': pd.read_excel
    }

    def __init__(self, path, filetype):
        self.path = path
        self.type = filetype
        self.data = None
        self.hosts = None
        self.load()

    def load(self):
        """Loads the data from path"""
        self.data = Data.READERS[self.type](self.path)
        return self.data

    def prepare(self, no_transforms=False):
        """Separates hosts and applies transformations to prepare data for use."""
        # Convert the columns to a common format - all lowercase, no spaces
        self.data.columns = self.data.columns.str.lower().str.replace(' ', '')

        # We need hosts in all cases
        self.find_hosts()

        # We do not want to transform data when using user-supplied models
        if not no_transforms:
            self.make_transforms()

        # Adjust dtypes or stuff will break later for some filetypes
        self.data = self.data.convert_dtypes()
        return self

    def make_transforms(self):
        """Applies transformations and removes unnecessary columns"""
        # Find the column labels used in the input dataset,
        # Reorder and rename them to match Data.COLUMNS[:, 0]
        columns = self.extract_feature_names()
        self.data = self.data.loc[:, columns]
        self.data.columns = [names[0] for names in Data.COLUMNS]

        # Calculate the additional features that will not be included
        self.add_features()

        # Sport and Dport have to be explicitly converted to strings
        self.data.loc[:, ['sport', 'dport']] = self.data \
            .loc[:, ['sport', 'dport']].astype(str)
        return self

    def find_hosts(self):
        """Locates the column with src addresses and extracts it into self.hosts"""
        names = ['srcaddr', 'srcaddress', 'sourceaddr', 'sourceaddress', 'host']
        for name in names:
            if name in self.data.columns:
                self.hosts = self.data.loc[:, [name]]
                self.data.drop(columns=[name])
                self.hosts.columns = ['srcaddr']
                return self
        raise ValueError('Unable to locate source addresses in data')

    def extract_feature_names(self):
        """Attempts to identify the required columns using aliases from Data.COLUMNS"""
        columns = self._get_columns(self.data.columns)
        return columns

    def _get_columns(self, cols):
        if isinstance(cols, pd.RangeIndex):
            return self._get_numeric(cols)
        else:
            try:
                return self._get_names(cols)
            except TypeError as e:
                raise TypeError('Invalid column type encountered:', e)

    def get_bitspersec(self):
        """Calculates bits per second"""
        totbytes = self.data['totbytes']
        duration = self.data['dur']
        return np.uint64(np.around((totbytes * 8) / duration))

    def add_features(self):
        """Calculates and adds additional data columns"""
        self.data['bps'] = self.get_bitspersec()

    def _get_numeric(self, cols):
        if len(cols) == len(Data.COLUMNS):
            return [i for i in range(len(Data.COLUMNS))]
        # If there are no names the exact number of columns is expected
        raise ValueError(f'Invalid number of columns: {len(cols)}, '
                         f'expected: {len(Data.COLUMNS)}')

    def _get_names(self, cols):
        colnames = []
        missing = []
        for column in Data.COLUMNS:
            found = False
            for name in column:
                if name in cols:
                    colnames.append(name)
                    found = True
                    break
            if not found:
                missing.append(column[0])

        if missing:
            raise KeyError(f'Missing column(s): {missing}')
        else:
            return colnames

    def batchify(self, num, batch_type):
        """Splits the data into a number of batches of equal sizes"""
        # Start by determining the number of batches
        n_rows = self.data.shape[0]
        if batch_type == '%':
            if not (0 < num < 100):
                raise ValueError(f'Invalid percentage of rows per batch: {num}')
            num /= 100
            n_batches = int(1 / num)
        elif batch_type == 'batches':
            n_batches = num
            if not (0 < n_batches < n_rows):
                m = (f'Invalid number of batches ({n_batches}). Must be positive '
                     f'and lower than the number of rows ({n_rows})')
                raise ValueError(m)
        else:
            raise ValueError(f'Invalid batch type: {batch_type}')

        # Actual batchifying starts here
        batches = [(i + 1) * (n_rows // n_batches) for i in range(n_batches)]
        batches = np.vsplit(self.data, batches)

        # Remove all empty batches if any show up
        batches = [i for i in batches if i.shape[0] != 0]

        return batches

    def __repr__(self):
        r = (
            f'{self.__class__.__name__} of shape: {self.data.shape} '
            f'with hosts {self.hosts.shape}'
        )
        return r
