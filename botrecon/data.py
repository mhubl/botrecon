import pandas as pd
import numpy as np


def get_data(path, type, no_transforms=False):
    return Data(path, type).prepare(no_transforms)


class Data(object):
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
        self.data = Data.READERS[self.type](self.path)
        return self.data

    def prepare(self, no_transforms=False):
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
        names = ['srcaddr', 'srcaddress', 'sourceaddr', 'sourceaddress']
        for name in names:
            if name in self.data.columns:
                self.hosts = self.data.loc[:, [name]]
                self.data.drop(columns=[name])
                self.hosts.columns = ['srcaddr']
                return self
        raise ValueError('No column containing source addresses')

    def extract_feature_names(self):
        columns = self._get_columns(self.data.columns)
        return columns

    def _get_columns(self, cols):
        if isinstance(cols, pd.RangeIndex):
            return self._get_numeric(cols)
        else:
            try:
                return self._get_names(cols)
            except TypeError as e:
                raise ValueError('Invalid column type encountered:\n', e)

    def get_bitspersec(self):
        totbytes = self.data['totbytes']
        duration = self.data['dur']
        return np.uint64(np.around((totbytes * 8) / duration))

    def add_features(self):
        self.data['bps'] = self.get_bitspersec()

    def _get_numeric(self, cols):
        if len(cols) == len(Data.COLUMNS):
            return [i for i in range(len(Data.COLUMNS))]
        # If there are no names the exact number of columns is expected
        raise ValueError(f'Invalid number of columns: {len(cols)}, '
                         f'expected: {len(Data.COLUMNS)}')

    def applyParallel(self, dfGrouped, func):
        from joblib import Parallel, delayed
        retLst = Parallel(n_jobs=-1)(delayed(func)(group)
                                     for name, group in dfGrouped)
        return pd.concat(retLst)

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

    def __repr__(self):
        r = (
            f'{self.__class__.__name__} of shape: {self.data.shape} '
            f'with hosts {self.hosts.shape}'
        )
        return r
