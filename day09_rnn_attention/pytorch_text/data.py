import collections
import glob
import torch
import numpy as np

from .preprocess import unicode_to_ascii
from .preprocess import ascii_to_onehot
from .preprocess import ascii_to_index_seq
from .utils import installpath


class SimpleDataset(torch.utils.data.Dataset):
    def __init__(self, x, y, lengths=None):
        super().__init__()
        self.x = x
        self.y = y
        self.lengths = lengths

    def __getitem__(self, idx):
        length = None if self.lengths is None else self.lengths[idx]
        return self.x[idx], self.y[idx], length

    def __len__(self):
        return len(self.x)


def load_name_data(directory=None, balanced=False):
    """
    Returns
    -------
    rawdata : list of tuple
        [(category, [name, name, ... ]),
         (category, [name, name, ... ]),
         ...
        ]
    balanced : Boolean
        If True, over-sampling to balance class distribution
    """
    if directory is None:
        directory = '{}/data/names/'.format(installpath)

    max_num_names = 0
    rawdata = []
    for path in glob.glob('{}/*.txt'.format(directory)):
        category = path.split('/')[-1][:-4]
        with open(path, encoding='utf-8') as f:
            names = [unicode_to_ascii(name.strip()) for name in f]
        max_num_names = max(max_num_names, len(names))
        rawdata.append((category, names))
    # over sampling
    if balanced:
        return_data = []
        for category, names in rawdata:
            num_names = len(names)
            if num_names == max_num_names:
                return_data.append((category, names))
                continue
            sample_indices = np.random.random_integers(0, high=num_names, size=max_num_names)
            over_sampled = [names[i] for i in sample_indices]
            return_data.append((category, over_sampled))
    else:
        return_data = rawdata
    return return_data

def load_name_data_as_dataset(as_image=False, image_len=19, balanced=False, directory=None):
    """
    Arguments
    ---------
    as_image : Boolean
        If True, it returns name which encoded as onehot image vector.
        False, it returns name which encoded as integer sequence.
    image_len : int
        If you set as_imgae True, you can specify the image length.
        Default is 19 which is the length of longest name

    Returns
    -------
    dataset : torch.utils.data.Dataset
    idx_to_category : list of str
        Category list

    Usage
    -----
        >>> dataset, idx_to_category = load_name_data_as_dataset(
                as_image=False, image_len=-1)
    """

    # load data
    namedata = load_name_data(directory, balanced)

    # prepare to transform Dataset
    category_to_idx = collections.defaultdict(lambda: len(category_to_idx))
    data = []

    for category, names in namedata:
        for name in names:
            # vectorize
            length = len(name)
            if as_image:
                # torch.FloatTensor
                xi = ascii_to_onehot(name, image_len)
            else:
                # torch.LongTensor
                xi = ascii_to_index_seq(name, image_len)
                xi = torch.LongTensor(xi)
            yi = category_to_idx[category]
            data.append((xi, yi, length))

    # as Dataset
    x, y, lengths = zip(*data)
    y = torch.LongTensor(y)
    lengths = torch.LongTensor(lengths)
    dataset = SimpleDataset(x, y, lengths)

    # wrap-up
    idx_to_category, _ = zip(*sorted(category_to_idx.items(), key=lambda x:x[1]))

    return dataset, idx_to_category