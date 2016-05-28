"""Querying module to prepare CDS data for Beard."""

import argparse
import re

from json import dumps

from itertools import count

from invenio.bibrecord import (
    field_get_subfield_values as get_subfield_values)
from invenio.search_engine import get_record, perform_request_search
from invenio.search_engine_utils import get_fieldvalues


# Consecutive id as a suffix for signature id
consecutive_id = count()


def create_signature_id(signature):
    """Create signature id for given signature."""
    return "{0}_{1}_{2}".format(
        signature["publication_id"],
        signature["author_name"],
        next(consecutive_id))


def is_collaboration(author_name):
    """Check, if author_name is a collaboration."""
    collaborations = [
        "collaboration",
        "collaborations",
        "colaboration",
        "colaborations"
        # "atlas",
        # "cms",
        # "lhc",
        # "lhcb"
    ]

    for collaboration in collaborations:
        if collaboration in author_name.lower():
            return True
    return False


def get_record_ids(
        search_pattern="100__a:/.*/ or 700__a:/.*/ and not 980__a:AUTHORITY"):
    """Get public bibliographic record ids from CDS.

    Uses perform_request_search from the Invenio's search engine module.

    :param str search_pattern: search pattern used for the request

    :return: list of integers (record-ids)
    """
    return perform_request_search(p=search_pattern)


def dump_signatures_and_records(
        output_signatures, output_records, record_ids=None):
    """Dump signatures and records to files.

    :param str output_signatures: path to JSON file to dump signatures
    :param str output_records: path to JSON file to dump records
    """
    if not record_ids:
        record_ids = get_record_ids()

    fp_signatures = open(output_signatures, "w")
    fp_records = open(output_records, "w")

    fp_signatures.write("[")  # Open list
    fp_records.write("[")  # Open list

    # No list seperator ',' for last item
    last_record_id = record_ids[-1]

    # Dump record and signatures for every given CDS record
    for record_id in record_ids:
        # Get meta data of given CDS record
        cds_record = get_record(record_id)

        try:
            if record_id == last_record_id:
                signatures = create_signatures(record_id, cds_record)
                if signatures:
                    # Dump signatures to file
                    previous_signature = None
                    for signature in signatures:
                        if previous_signature is not None:
                            fp_signatures.write(dumps(previous_signature) + ",")
                        previous_signature = signature

                    # Dump last signature to file
                    fp_signatures.write(dumps(previous_signature))

                    # Dump last record to file
                    record = create_record(record_id, cds_record)
                    fp_records.write(dumps(record))
            else:
                signatures = create_signatures(record_id, cds_record)
                if signatures:
                    # Dump signatures to file
                    for signature in signatures:
                        fp_signatures.write(dumps(signature) + ",")

                    # Dump record to file
                    record = create_record(record_id, cds_record)
                    fp_records.write(dumps(record) + ",")
        except UnicodeDecodeError as e:
            print "Error: incorrect record '{0}'. ({1})".format(
                record_id, e)

    fp_signatures.write("]")  # Close list
    fp_records.write("]")  # Close list

    fp_signatures.close()
    fp_records.close()


def get_signatures(record_ids=None):
    """Get all signatures from given list of record_ids."""
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


def get_records(record_ids=None):
    """Get all records from given list of record_ids."""
    if not record_ids:
        record_ids = get_record_ids()
    print "{0} record-ids requested.".format(len(record_ids))

    # Get all records
    records = []
    for record_id in record_ids:
        record = create_record(record_id)
        if record:
            records.append(record)
    print "{0} records created.".format(len(records))

    return records


def create_record(record_id, cds_record=None):
    """Create the record for the given cds_record.

    record_id has to exist.

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
    if not cds_record:
        cds_record = get_record(record_id)

    # List 'authors' containing in author and co-authors
    # [0]: Author (can also be 'None' or a collaboration)
    # [1:]: Co-authors (if any)
    authors = []
    authors.extend(cds_record.get("100", []))  # Author
    authors.extend(cds_record.get("700", []))  # Co-authors

    # Get author's full names of given cds_record
    author_names = []
    for author in authors:
        author_names.extend(get_subfield_values(author, "a"))

    # Filter collaborations
    author_names = [
        name for name in author_names if not is_collaboration(name)]

    if author_names:
        # Get title of given cds_record
        try:
            field = cds_record.get("245", [])[0]
            title = get_subfield_values(field, "a")[0]
        except IndexError:
            title = ""

        # Get (earliest) year of publication of given cds_record
        try:
            field = cds_record.get("260", [])[0]
            subfield = get_subfield_values(field, "c")[0]
            year = re.findall(r'[0-9]{4}', subfield)[0]
        except IndexError:
            year = False

        # Return record
        return {
            "publication_id": str(record_id),
            "authors": author_names,
            "title": title,
            "year": year
        }

    return None


def get_authority_ids(author):
    """Get authority ids for given author.

    Consider subfields '0', 'h', 'i', and 'j' from fiven 'author' field.

    :param tuple author: representing an author's datafield
        Example:
            from invenio.search_engine import get_record
            cds_record = get_record(2132991)
            author = cds_record["100"][0]

    :return: dictionary can contain following keys: cern_id, inspire_id,
        and cds_id. Its value represents the id, which in any case is a
        sequence of numbers only. Empty dictionary {} is returned if no
        authority ids have been found
        Example:
            {'inspire': '00146525'}
    """
    subfield_values = []
    subfield_values.extend(get_subfield_values(author, "0"))
    subfield_values.extend(get_subfield_values(author, "h"))
    subfield_values.extend(get_subfield_values(author, "i"))
    subfield_values.extend(get_subfield_values(author, "j"))

    # Contains authority ids "cern_id", "inspire_id", and "cds_id" (if any)
    result = {}

    # Lower case required
    # {"prefix found in 'author' subfield": "prefix normalized"}
    prefixes = {
        'cern-': 'cern',
        'ccid-': 'cern',
        'author|(szgecern)': 'cern',
        'inspire-': 'inspire',
        'author|(inspire)inspire-': 'inspire',
        'cds-': 'cds',
        'author|(cds)': 'cds'
    }

    for subfield in subfield_values:
        for prefix in prefixes.iterkeys():
            subfield = subfield.lower()
            id_ = subfield.replace(prefix, "")
            if subfield.startswith(prefix) and id_:
                # Type of authority id
                prefix_normalized = prefixes[prefix]
                if prefix_normalized == "cern":
                    result["cern_id"] = id_
                elif prefix_normalized == "inspire":
                    result["inspire_id"] = id_
                elif prefix_normalized == "cds":
                    result["cds_id"] = id_

    return result


def create_signatures(record_id, cds_record=None):
    """Create signatures for the given record_id.

    A dictionary is representing a signature. A signature always contains the
    following four attributes, where its values are strings:
        'signature_id': unique id
        'publication_id': record id the signature has been created from
        'author_affiliation': affiliation(s)
            (no affiliation: empy string '',
             multiple affiliation: 'a_0 a_1 ...')
        'author_name': full name

    A signature can contain authority ids, represented by up to three
    attributes:
        'author_cern_id': CERN/CCID id
        'author_inspire_id': INSPIRE-HEP id
        'author_cds_id': CDS id

    :param int record_id: record-id
        Example 1:
            record_id = 1543296
        Example 2:
            record_id = 2050951

    :return: list of dictionaries representing the signatures. Empty list, if
        no authors found or record is part of a collaboration only
        Example 1:
            [{'publication_id': '1543296',
              'signature_id': '1543296_Ellis, John_2',
              'author_affiliation': "King's Coll. London CERN",
              'author_name': 'Ellis, John'},
             ...]
        Example 2:
            [{'publication_id': '2050951',
              'author_cern_id': '678846',
              'author_inspire_id': '00374510',
              'author_name': 'Martin, Christopher Blake',
              'signature_id': '2050951_Martin, Christopher Blake_0',
              'author_affiliation': 'Johns Hopkins U.'},
             ...]
    """
    signatures = []  # Signatures of authors and co-authors

    if not cds_record:
        cds_record = get_record(record_id)

    # List 'authors' containing in author and co-authors
    # [0]: Author (can also be 'None' or a collaboration)
    # [1:]: Co-authors (if any)
    authors = []
    authors.extend(cds_record.get("100", []))  # Author
    authors.extend(cds_record.get("700", []))  # Co-authors

    # Author and co-authors are processed the same
    for author in authors:
        try:
            author_name = get_subfield_values(author, "a")[0]

            # If author is a collaboration, no signature will be created
            if is_collaboration(author_name):
                # Continue with next author (if any)
                break

            # Create signature representing author's meta data
            signature = {}

            # Add record id
            signature["publication_id"] = str(record_id)

            # Add full name
            signature["author_name"] = author_name

            # Add affiliation(s) (if any)
            author_affiliation = " ".join(get_subfield_values(author, "u"))
            if author_affiliation:
                signature["author_affiliation"] = author_affiliation
            else:
                signature["author_affiliation"] = ""

            # Add authority ids for given author (if any)
            authority_ids = get_authority_ids(author)
            try:
                signature["author_cern_id"] = authority_ids["cern_id"]
            except KeyError:
                pass
            try:
                signature["author_inspire_id"] = authority_ids["inspire_id"]
            except KeyError:
                pass
            try:
                signature["author_cds_id"] = authority_ids["cds_id"]
            except KeyError:
                pass

            # Add signature id
            signature["signature_id"] = create_signature_id(signature)

            # Append signature to signatures
            signatures.append(signature)
        except IndexError:
            # No subfield 'a' has been found, hence no signature will be
            # created for the given author
            pass

    return signatures

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_signatures", required=True, type=str)
    parser.add_argument("--output_records", required=True, type=str)
    args = parser.parse_args()

    dump_signatures_and_records(args.output_signatures, args.output_records)

