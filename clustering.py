"""Clustering module to cluster records and signatures by phonetic blocks.

Export the clustered records and signatures using the utils module and run
beard on this set of data.

Requires Beard installation.
"""

from querying import (
    create_record,
    create_signatures,
    get_record_ids,
    get_signatures)

try:
    from invenio.search_engine_utils import get_fieldvalues
except ImportError:
    import sys
    sys.path.extend([
        "/usr/lib64/python2.6/site-packages/",
        "/usr/lib/python2.6/site-packages/"])
    from invenio.search_engine_utils import get_fieldvalues

from beard.clustering import block_phonetic

from numpy import np


def memoize(fn):
    """Memoize fn with public cache."""
    cache = {}

    def memoizer(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]

    return memoizer


def create_signature_blocks(record_id):
    """Create signature blocks given the record_id.

    :param int record_id: record-id
        Example:
            record_id = 1369415

    :return: list of strings representing phonetic blocks for author's and
        co-author's full names. Empty list, if no author's found
        Example:
            [u'ELj', u'MCLAGHLANm', u'VARBASTj']
    """
    signature_blocks = []

    author = get_fieldvalues(record_id, "100__a")
    coauthors = get_fieldvalues(record_id, "700__a")

    authors = []
    authors.extend(author)
    authors.extend(coauthors)

    for author in authors:
        signature_block = create_signature_block(author)
        if signature_block:
            signature_blocks.append(signature_block)

    return signature_blocks


def create_signature_block(author_name):
    """Create signature block for given author_name.

    :param str author_name: author's full name
        Example:
            author_name = "Ellis, John R"

    :return: string representing phonetic block for full_name
        Example:
            u'ELj'
    """
    try:
        name = {'author_name': author_name}
        signature_block = block_phonetic(
            np.array([name], dtype=np.object).reshape(-1, 1),
            threshold=0,
            phonetic_algorithm='nysiis')
        return signature_block[0]
    except (IndexError, KeyError) as err:
        print "Couldn't create signature: {0} in '{1}'".format(err, name)


def block_clustering(record_ids=None):
    """Cluster signatures and records by author's full name phonetic blocks.

    Creates signatures and records given the record-ids. For each author's
    full name, a phonetic block is created. The signatures and records are
    clustered by the phonetic blocks in which they occur.

    :param list record_ids: list of record-ids classified for clustering.
        Requests record-ids if None
        Example:
            record_ids = [1369415, 1638463, 1112288, 1181000]

    :return: tuple of dictionaries, representing clustered records and
        signatures clustered by phonetic blocks (in this order)
        Example:
            ({u'ELj': [{'publication_id': '1369415',
                         'collaboration': False,
                         'title': 'The ...',
                         'year': '2011',
                         'authors': ['Ellis, J', 'McLaughlin, M A', ...]},
                        ...],
              u'MCLAGHLANm': ...,
              u'RACLAFa': ...,
              ...},
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
              ...})
    """
    if not record_ids:
        record_ids = get_record_ids()

    signatures = get_signatures(record_ids)
    signatures_by_blocks = block_clustering_signatures(signatures)
    records_by_blocks = block_clustering_records(signatures_by_blocks)
    return records_by_blocks, signatures_by_blocks


def block_clustering_signatures(signatures):
    """Cluster signatures by author's full name phonetic blocks.

    :param list signatures: list of signatures
        Example:
            [{'publication_id': '1369415',
              'signature_id': '1369415_Ellis, J',
              'author_affiliation': '',
              'author_name': 'Ellis, J'},
             {'publication_id': '1369415',
              'signature_id': '1369415_McLaughlin, M A',
              'author_affiliation': '',
              'author_name': 'McLaughlin, M A'},
             ...]

    :return: dictionary, representing clustered signatures by phonetic blocks
        Example:
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
             ...}

    """
    # For each phonetic block, get signatures
    signatures_by_blocks = {}
    create_signature_block_memoized = memoize(create_signature_block)
    for signature in signatures:
        phonetic_block = create_signature_block_memoized(
            signature["author_name"])

        if phonetic_block:
            if phonetic_block in signatures_by_blocks:
                signatures_by_blocks[phonetic_block].append(signature)
            else:
                signatures_by_blocks[phonetic_block] = [signature]
    print "{0} signature cluster created.".format(len(signatures_by_blocks))

    return signatures_by_blocks


def block_clustering_records(signatures_by_blocks):
    """Cluster records by author's full name phonetic blocks.

    :param dict signatures_by_blocks: dictionary, representing clustered
        signatures by phonetic blocks
        Example:
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

    :return: dictionary, representing clustered records by phonetic blocks
        Example:
            {u'ELj': [{'publication_id': '1369415',
                       'collaboration': False,
                       'title': 'The ...',
                       'year': '2011',
                       'authors': ['Ellis, J', 'McLaughlin, M A', ...]},
                      ...],
             u'MCLAGHLANm': ...,
             u'RACLAFa': ...,
             ...}
    """
    # For each phonetic block, get records
    create_record_memoized = memoize(create_record)
    records_by_blocks = {}
    for phonetic_block in signatures_by_blocks:
        signatures = signatures_by_blocks[phonetic_block]
        record_ids = set()
        for signature in signatures:
            record_ids.add(signature["publication_id"])
        records_by_blocks[phonetic_block] = []
        for record_id in record_ids:
            record = create_record_memoized(record_id)
            records_by_blocks[phonetic_block].append(record)
    print "{0} record clusters created.".format(len(records_by_blocks))

    return records_by_blocks

