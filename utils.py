"""Set of utility functions."""

try:
    import cPickle as pickle
except:
    import pickle

from json import dump, load

from os.path import join


def dump_to_pickle(data, dest):
    """Write a pickled representation of data and dump to given dest."""
    try:
        with open(dest, "w") as f:
            pickle.dump(data, f, -1)
    except (EnvironmentError, IOError, ValueError) as e:
        print e


def load_pickle(src):
    """Load dumped and pickled data in given src."""
    data = None
    try:
        with open(src) as f:
            data = pickle.load(f)
    except (EnvironmentError, IOError, ValueError) as e:
        print e

    return data


def dump_to_json(data, dest):
    """Write data to given dest in a json-format."""
    try:
        with open(dest, "w") as f:
            dump(data, f)
    except (EnvironmentError, IOError, ValueError) as e:
        print e


def dump_to_json_by_blocks(data, filepath, filename):
    """Write data to multiple json files, splitted by clusters.
    
    Example:
        ELj_records.json
        MCLAGHLANm_records.json
        RACLAFa_records.json

    :param dict data: dictionary, representing records or signatures clusted
        by phonetic blocks (key)
        Example (clusted records):
            {u'ELj': [{'publication_id': '1369415',
                       'signature_id': '1369415_Ellis, J',
                       'author_affiliation': '',
                       'author_name': 'Ellis, J'},
                      {'publication_id': '1638463',
                       'signature_id': '1638463_Ellis, John',
                       'author_affiliation': "King's Coll. London CERN",
                       'author_name': 'Ellis, John'},
                      ...],
             u'MCLAGHLANm': ...,
             u'RACLAFa': ...,
             ...}
    :param str filepath: destination directory
        Example:
            filepath = "/tmp/clustering/records"
    :param str filename: filename, without the extension
        Example:
            filename = "records"
    """
    for key, value in data.iteritems():
        # Update filename
        _filename = "{0}_{1}.json".format(key, filename)
        dump_to_json(value, join(filepath, _filename))


def load_json(src):
    """Load json in given src."""
    data = None
    try:
        with open(src) as f:
            data = load(f)
    except (EnvironmentError, IOError, ValueError) as e:
        print e

    return data

