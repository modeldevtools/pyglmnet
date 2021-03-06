"""
A set of convenience functions to download datasets for illustrative examples
"""
import os
import os.path as op
import sys
import itertools
import numpy as np
from scipy.special import comb
from urllib.request import urlretrieve

_rgcs_license_text = """
License
-------

This tutorial dataset (RGC spikes data) is granted by
original authors (E.J. Chichilnisky and Jonathan Pillow).
The dataset ramains a property of the original authors.
Its use and transfer outside tutorial, e.g. for research purposes,
is prohibited without written consent to the original authors.

If you reference this dataset in your publications, please:
    1) acknowledge the authors: E.J. Chichilnisky and Jonathan Pillow
    2) cite the publications as indicated in the tutorial

If you want to use it beyond the educational
purposes or have further questions, please contact
Jonathan Pillow (pillow@princeton.edu).
"""


def _reporthook(count, block_size, total_size):
    """Report download percentage."""
    # https://blog.shichao.io/2012/10/04/progress_speed_indicator_for_urlretrieve_in_python.html  # noqa

    if count == 0 or count * block_size >= total_size:
        print('')
    progress_size = int(count * block_size)
    percent = min(int(count * block_size * 100 / total_size), 100)
    sys.stdout.write("\r...%d%%, %d MB"
                     % (percent, progress_size / (1024 * 1024)))


def get_data_home(data_home=None):
    """Return the path of the pyglmnet data dir.

    Function from scikit-learn.

    This folder is used by some large dataset loaders to avoid downloading the
    data several times.

    By default the data dir is set to a folder named 'glm_data' in the
    user home folder.

    Parameters
    ----------
    data_home : str | None
        The path to pyglmnet data dir.
    """
    if data_home is None:
        data_home = op.join('~', 'glm_data')
    data_home = op.expanduser(data_home)
    if not op.exists(data_home):
        os.makedirs(data_home)
    return data_home


def fetch_tikhonov_data(dpath=None):
    """Downloads data for Tikhonov example.

    Parameters
    ----------
    dpath: str | None
        specifies path to which the data files should be downloaded.
        default: None

    Returns
    -------
    dpath : str
        The data path to Tikhonov dataset
    """
    dpath = get_data_home(data_home=dpath)
    fnames = ['fixations.csv', 'probes.csv', 'spiketimes.csv']

    if not (op.isdir(dpath) and all(op.exists(op.join(dpath, fname))
                                    for fname in fnames)):
        base_url = (
            "https://raw.githubusercontent.com/glm-tools/datasets/master"
        )
        fnames = ['fixations.csv', 'probes.csv', 'spiketimes.csv']

        for fname in fnames:
            url = base_url + "/tikhonov/" + fname
            fname = os.path.join(dpath, fname)
            urlretrieve(url, fname, _reporthook)

    return dpath


def fetch_community_crime_data(dpath=None):
    """Downloads community crime data.

    This function removes missing values, extracts features, and
    returns numpy arrays

    Parameters
    ----------
    dpath: str | None
        specifies path to which the data files should be downloaded.
        default: None

    Returns
    -------
    X: numpy array
        (n_samples x n_features)
    y: numpy array
        (n_samples,)
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError('The pandas module is required for reading the '
                          'community crime dataset')

    dpath = get_data_home(data_home=dpath)
    file_name = 'communities.csv'

    if not (op.isdir(dpath) and op.exists(op.join(dpath, file_name))):
        fname = os.path.join(dpath, file_name)
        base_url = (
            "http://archive.ics.uci.edu/ml/machine-learning-databases"
        )
        url = base_url + "/" + "communities/communities.data"

        urlretrieve(url, fname, _reporthook)

        # Read in the file
        df = pd.read_csv(fname, header=None)

    df = pd.read_csv(op.join(dpath, file_name), header=None)

    # Remove missing values
    df.replace('?', np.nan, inplace=True)
    df.dropna(inplace=True, axis=1)
    df.dropna(inplace=True, axis=0)
    df.reset_index(inplace=True, drop=True)

    # Extract predictors and target from data frame
    X = np.array(df[df.keys()[range(3, 102)]])
    y = np.array(df[127])

    return X, y


def fetch_rgc_spike_trains(dpath=None, accept_rgcs_license=False):
    """Downloads data for spike trains prediction in retinal ganglia cells.

    Parameters
    ----------
    dpath: str
        specifies path to which the data files should be downloaded.
        default: None
    accept_rgcs_license: bool
        specify to true to accept the license to use the dataset
        default: False

    Returns
    -------
    dpath : str | None
        The data path for retinal ganglia cells dataset

    Note
    ----
    See https://github.com/glm-tools/datasets/RGCs/ for permission
    to use the dataset.
    """
    dpath = get_data_home(data_home=dpath)
    file_name = 'data_RGCs.json'

    # if file already exist, read it from there
    if not (op.isdir(dpath) and op.exists(op.join(dpath, file_name))):
        # accept licence
        if accept_rgcs_license:
            answer = 'y'
        else:
            answer = input('%s\nAgree (y/[n])? ' % _rgcs_license_text)
        if answer.lower() != 'y':
            raise RuntimeError('You must agree to the license to use this '
                               'dataset')

        base_url = (
            "https://raw.githubusercontent.com/glm-tools/datasets/master"
        )
        fnames = ['data_RGCs.json']
        for fname in fnames:
            url = base_url + "/RGCs/" + fname
            fname = os.path.join(dpath, fname)
            urlretrieve(url, fname, _reporthook)

    return dpath


def fetch_group_lasso_data(dpath=None):
    """Downloads and formats data needed for the group lasso example.

    Parameters
    ----------
    dpath: str | None
        specifies path to which the data files should be downloaded.

    Returns
    -------
    X: numpy array, shape (n_samples, n_features)
        The design matrix.
    y: numpy array, shape (n_samples,)
        The labels.
    group: list
        list of group indicies, the value of the ith position in the list
        is the group number for the ith regression coefficient
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError('The pandas module is required for the '
                          'group lasso dataset')

    # helper functions

    def find_interaction_index(seq, subseq,
                               alphabet="ATGC",
                               all_possible_len_n_interactions=None):
        n = len(subseq)
        alphabet_interactions = \
            [set(p) for
             p in list(itertools.combinations_with_replacement(alphabet, n))]

        num_interactions = len(alphabet_interactions)
        if all_possible_len_n_interactions is None:
            all_possible_len_n_interactions = \
                [set(interaction) for
                 interaction in
                 list(itertools.combinations_with_replacement(seq, n))]

        subseq = set(subseq)

        group_index = num_interactions * \
            all_possible_len_n_interactions.index(subseq)
        value_index = alphabet_interactions.index(subseq)

        final_index = group_index + value_index
        return final_index

    def create_group_indicies_list(seqlength=7,
                                   alphabet="ATGC",
                                   interactions=[1, 2, 3],
                                   include_extra=True):
        alphabet_length = len(alphabet)
        index_groups = []
        if include_extra:
            index_groups.append(0)
        group_count = 1
        for inter in interactions:
            n_interactions = comb(seqlength, inter)
            n_alphabet_combos = comb(alphabet_length,
                                     inter,
                                     repetition=True)

            for x1 in range(int(n_interactions)):
                for x2 in range(int(n_alphabet_combos)):
                    index_groups.append(int(group_count))

                group_count += 1
        return index_groups

    def create_feature_vector_for_sequence(seq,
                                           alphabet="ATGC",
                                           interactions=[1, 2, 3]):
        feature_vector_length = \
            sum([comb(len(seq), inter) *
                 comb(len(alphabet), inter, repetition=True)
                 for inter in interactions]) + 1

        feature_vector = np.zeros(int(feature_vector_length))
        feature_vector[0] = 1.0
        for inter in interactions:
            # interactions at the current level
            cur_interactions = \
                [set(p) for p in list(itertools.combinations(seq, inter))]
            interaction_idxs = \
                [find_interaction_index(
                 seq, cur_inter,
                 all_possible_len_n_interactions=cur_interactions) + 1
                 for cur_inter in cur_interactions]
            feature_vector[interaction_idxs] = 1.0

        return feature_vector

    positive_url = (
        "http://hollywood.mit.edu/burgelab/maxent/ssdata/MEMset/train5_hs"
    )
    negative_url = (
        "http://hollywood.mit.edu/burgelab/maxent/ssdata/MEMset/train0_5_hs"
    )

    dpath = get_data_home(data_home=dpath)
    fnames = ['pos', 'neg']
    if not (op.isdir(dpath) and all(op.exists(op.join(dpath, fname))
                                    for fname in fnames)):
        pos_file = os.path.join(dpath, 'pos')
        neg_file = os.path.join(dpath, 'neg')
        urlretrieve(positive_url, pos_file, _reporthook)
        urlretrieve(negative_url, neg_file, _reporthook)
    else:
        pos_file = os.path.join(dpath, 'pos')
        neg_file = os.path.join(dpath, 'neg')

    with open(pos_file) as posfp:
        positive_sequences = [str(line.strip().upper()) for idx, line in
                              enumerate(posfp.readlines())
                              if ">" not in line and idx < 2 * 8000]

    with open(neg_file) as negfp:
        negative_sequences = [str(line.strip().upper()) for idx, line in
                              enumerate(negfp.readlines())
                              if ">" not in line and
                              idx < 2 * len(positive_sequences)]

    assert len(positive_sequences) == len(negative_sequences), \
        "lengths were not the same: p={pos} n={neg}" \
        .format(pos=len(positive_sequences), neg=len(negative_sequences))

    positive_vector_matrix = np.array([create_feature_vector_for_sequence(s)
                                       for s in positive_sequences])
    negative_vector_matrix = np.array([create_feature_vector_for_sequence(s)
                                       for s in negative_sequences])

    df = pd.DataFrame(data=np.vstack((positive_vector_matrix,
                                      negative_vector_matrix)))
    df.loc[0:len(positive_vector_matrix), "Label"] = 1.0
    df.loc[len(positive_vector_matrix):, "Label"] = 0.0

    X = df[df.columns.difference(["Label"])].values
    y = df.loc[:, "Label"].values
    group = create_group_indicies_list()

    return X, y, group
