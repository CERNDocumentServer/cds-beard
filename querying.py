"""Querying module to prepare CDS data for block clustering and beard."""

import numpy as np
import re

from beard.clustering import block_phonetic

from itertools import count

from json import load

try:
    from invenio.bibfield import get_record
    from invenio.search_engine import perform_request_search
    from invenio.search_engine_utils import get_fieldvalues
except ImportError:
    # Access Invenio modules inside conda environment
    import sys
    sys.path.extend([
        "/usr/lib64/python2.6/site-packages/",
        "/usr/lib/python2.6/site-packages/"])
    from invenio.bibfield import get_record
    from invenio.search_engine import perform_request_search
    from invenio.search_engine_utils import get_fieldvalues


consecutive_id = count()


def _get_record(record_id, source):
    """Get filtered record based on source."""
    record_full = get_record(record_id)
    record = {}

    for attr in source:
        try:
            record[attr] = record_full[attr]
        except (KeyError, TypeError):
            pass

    return record


def _create_signature_id(record_id, author):
    """Create signature-id for author in record with record_id."""
    return "{0}_{1}_{2}".format(str(record_id), author, next(consecutive_id))


def _create_signature(record_id, author):
    """Create signature for author in record with record_id."""
    author_affiliation = []
    
    try:
        affiliations = author["affiliation"]
        # affiliations can be a str (single affiliation) or
        # a list (multiple affiliations)
        if type(affiliations) == str:
            author_affiliation.append(affiliations)
        else:
            author_affiliation.extend(affiliations)
    except KeyError:
        pass

    return {
        "signature_id": _create_signature_id(
            record_id, author["full_name"]),
        "publication_id": str(record_id),
        "author_name": author["full_name"],
        "author_affiliation": " ".join(author_affiliation)
    }


def _is_collaboration(full_name):
    """Check, if author's full_name is a collaboration and not a person."""
    collaborations = (
        "collaboration",
        "collaborations",
        "colaboration",
        "colaborations",
        "atlas",
        "cms"
        "lhc"
        "lhcb"
    )

    for collaboration in collaborations:
        if collaboration in full_name.lower():
            return True
    return False


def get_record_ids(
        search_pattern="100__a:/.*/ or 700__a:/.*/ and not 980__a:AUTHORITY"):
    """Get public bibliographic record-ids from CDS.

    Uses perform_request_search from the Invenio's search engine module.
    
    :param str search_pattern: search pattern used for the request
    :return: list of integers (record-ids)
    """
    return perform_request_search(p=search_pattern)


def get_signatures(record_ids=None):
    """Get all signatures from given record_ids."""
    # Get all record-ids for clustering
    if not record_ids:
        record_ids = get_record_ids()
    print "{0} record-ids requested.".format(len(record_ids))
    
    # Get all signatures
    signatures = []
    for record_id in record_ids:
        signatures.extend(create_signatures(record_id))
    print "{0} signatures created.".format(len(signatures))

    return signatures


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


def create_signature_block(full_name):
    """Create signature block given author's full_name.
    
    :param str full_name: author's full name
        Example: 
            full_name = "Ellis, John R"
    
    :return: string representing phonetic block for full_name
        Example:
            u'ELj'
    """
    try:
        name = {'author_name': full_name}
        signature_block = block_phonetic(
            np.array([name], dtype=np.object).reshape(-1, 1),
            threshold=0,
            phonetic_algorithm='nysiis')
        return signature_block[0]
    except (IndexError, KeyError) as err:
        print "Couldn't create signature: {0} in '{1}'".format(err, name)


def create_record(record_id):
    """Create record given the record_id.
    
    :param int record_id: record-id
        Example:
            record_id = 1369415

    :return: dictionary representing the record. None, if no authors found or
        record is part of a collaboration only
        Example:
            {'publication_id': '1369415',
             'collaboration': False,
             'title': 'The impact of a stochastic gravitational-wave background
                 on pulsar timing parameters',
             'year': '2011',
             'authors': ['Ellis, J', 'McLaughlin, M A', 'Verbiest, J P W']}
    """
    source = [
        "authors.full_name",  # author (and co-authors)
        "title.title",
        "imprint.date"  # year of publication
    ]
   
    response = _get_record(record_id, source)
   
    # Get the (earliest) year of publication of the given paper.
    try:
        year = response["imprint.date"]
        # If multiple 260__c fields, use 1st year in list
        if type(year) == list:
            year = year[0]
        
        year = re.findall(r'[0-9]{4}', year)[0]
    except (KeyError, IndexError):
        year = False
    
    try:
        # Filter 'None' values in authors and collaborations
        # Example: a record has field 700 (co-author) but no 100 (author),
        # 'authors': [None, ...]; or
        # the record is part of a collaboration, like "ATLAS Collaboration"
        authors = [
            author for author in response["authors.full_name"] if
            author and
            not _is_collaboration(author)]
        
        # Return record if given paper contains "real" authors only
        if authors: 
            return {
                "publication_id": str(record_id),
                "authors": authors,
                "title": response.get("title.title", ""),
                "year": year
            }
    except KeyError:
        pass

    return None


def create_signatures(record_id):
    """Create signatures for the given record_id.
    
    :param int record_id: record-id
        Example:
            record_id = 1543296

    :return: list of dictionaries representing the signatures. Empty list, if
        no authors found or record is part of a collaboration only
        Example:
            [{'publication_id': '1543296',
              'signature_id': '1543296_Ellis, John',
              'author_affiliation': "King's Coll. London CERN",
              'author_name': 'Ellis, John'},
              ...]
    """
    source = [
        "authors"
    ]
 
    response = _get_record(record_id, source)
    signatures = []

    try:
        # Filter 'None' values and collaborations
        authors = [
            author for author in response["authors"] if
            author["full_name"] and
            not _is_collaboration(author["full_name"])]

        for author in authors:
            signatures.append(_create_signature(record_id, author))
    except KeyError:
        pass
    
    return signatures

