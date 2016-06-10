"""Helper to create look-up giving a `CERN People` collection dump.

The look-up is used for linking Beard clusters to CDS profiles by matching
authority ids. It allows to look-up the record id for an author profile by
giving a authority id.

Example:
    lookup['AUTHOR|(SzGeCERN)389900'] --> '2108556'
    lookup['AUTHOR|(INSPIRE)INSPIRE-00146525'] --> '2108556'
    lookup['AUTHOR|(CDS)2108556'] --> '2108556'
"""

import argparse

from json import dump, load


def get_authority_ids(record):
    """Get authority ids (system control numbers) of given record.

    Additionally, the record id (recid) is extracted as CDS authority id,
    e.g. '2108556' -> 'AUTHOR|(CDS)2108556'.

    :param dict record: representing meta data of the record
        Example:
            from invenio.bibfield import get_record
            record = get_record(2108556)

    :return: list of strings representing the authority ids. Empty list []
        if no id has been found
        Example:
            ['AUTHOR|(SzGeCERN)389900', 'AUTHOR|(INSPIRE)INSPIRE-00146525']
    """
    result = []
    authority_ids = record["system_control_number"]
    if isinstance(authority_ids, dict):
        result.append(authority_ids)

    elif isinstance(authority_ids, list):
        result.extend(authority_ids)

    result = [item["value"] for item in result]

    # Add recid as CDS authority id
    result.append("AUTHOR|(CDS){0}".format(record["recid"]))

    return result


def create_lookup(input_people, output_lookup):
    """Create look-up for people and dump to JSON file.

    Allows to look-up for a CDS profile id by giving a authority id.

    :param str input_people: file path to a JSON file containing a
        `CERN People` collection dump.
        File contains a dictionary in the format:
            {record_id: get_record(record_id), ...}, where get_record
            belongs the invenio.bibfield
    :param str output_lookup: file path to the output file
        File contains a dictionary in the format:
            {'AUTHOR|(SzGeCERN)389900': 2108556,
             'AUTHOR|(INSPIRE)INSPIRE-00146525': 2108556, ...}
    """
    with open(input_people) as f:
        people = load(f)

    result = {}

    for record_id, record in people.iteritems():
        authority_ids = get_authority_ids(record)
        for authority_id in authority_ids:
            result[authority_id] = record_id

    with open(output_lookup, "w") as f:
        dump(result, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_people", required=True, type=str,
                        help="Dump of records of the 'CERN People' collection")
    parser.add_argument("--output_lookup", required=True, type=str,
                        help="Created look-up for authority ids of CERN People")
    args = parser.parse_args()

    create_lookup(args.input_people, args.output_lookup)

