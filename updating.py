"""Updating module to update and upload CDS records."""

import argparse

from json import load
from os.path import join

from invenio.bibtask import task_low_level_submission
from invenio.search_engine import get_record
from invenio.bibrecord import (
    field_add_subfield, field_xml_output,
    record_get_field_instances, field_get_subfield_values)


def extend_author_field(author_field, cds_id):
    """Extend author datafield by CDS authority id and Beard tag.

    Extends the author datafield by the MARC subfields
        $$0:AUTHOR|(CDS)<cds_id>
        $$9:#BEARD#
    if $$0:AUTHOR|(CDS)<cds_id> does not exist in `author_field`.

    :param author_field:
        Example:
            # from invenio.search_engine import get_record
            # from invenio.bibrecord import record_get_field_instances
            # record = get_record(2150939)
            # author_field = record_get_field_instances(record, "100")[0]
            author_field = ([('a', 'Ellis, John'),
                             ('u', "King's Coll. London"),
                             ('u', 'CERN')], ' ', ' ', '', 32)
    :param str cds_id: sequence of numbers representing the CDS id
        Example:
            cds_id = '2108556'

    :result:
        Example:
            author_field = ([('a', 'Ellis, John'),
                             ('u', "King's Coll. London"),
                             ('u', 'CERN'),
                             ('0', 'AUTHOR|(CDS)2108556'),
                             ('9', '#BEARD#')], ' ', ' ', '', 32)

    :return: True, if `author_field` has been  updated, False otherwise
    """
    cds_authority_id = "AUTHOR|(CDS){0}".format(cds_id)
    if cds_authority_id not in field_get_subfield_values(author_field, '0'):
        field_add_subfield(author_field, "0", cds_authority_id)
        field_add_subfield(author_field, "9", "#BEARD#")
        return True

    return False


def update_record(record_id, authors):
    """Update authors in CDS record.

    :param int record_id: record to update author datafields
        Example:
            record_id = 2150939
    :param dict authors: dictionary where keys are author full names and
        values the CDS profile ids to be updated in the given record
        Example:
            authors = {'Ellis, John': '2108556'}

    :return: string representing the record XML element containing
        author (`100`) and/or co-author (`700`) datafields.
        Example:
            '<record>
                <controlfield tag="001">2150939</controlfield>
                <datafield tag="100" ind1=" " ind2=" ">
                    <subfield code="a">Ellis, John</subfield>
                    <subfield code="u">King's Coll. London</subfield>
                    <subfield code="u">CERN</subfield>
                    <subfield code="0">AUTHOR|(CDS)2108556</subfield>
                    <subfield code="9">#BEARD#</subfield>
                </datafield>
            </record>'
    """
    record = get_record(record_id)
    record_author = record_get_field_instances(record, "100")
    record_coauthors = record_get_field_instances(record, "700")

    if len(record_author) > 1:
        print ("Oops: several '100' (main author) fields have been found in"
               "record '{0}'".format(record_id))
        return ""

    datafields = ""
    author = False
    for author_field in record_author:
        author_name = field_get_subfield_values(author_field, 'a')[0]
        try:
            cds_id = authors[author_name]
            if extend_author_field(author_field, cds_id):
                datafields += field_xml_output(author_field, "100")
                author = True
        except KeyError:
            pass

    if len(authors) > 1 or not author:
        for coauthor_field in record_coauthors:
            coauthor_name = field_get_subfield_values(coauthor_field, 'a')[0]
            try:
                cds_id = authors[coauthor_name]
                if extend_author_field(coauthor_field, cds_id):
                    author = True
            except KeyError:
                pass
            datafields += field_xml_output(coauthor_field, "700")

    # Nothing to update
    if not author:
        print "No authors to update in record '{0}'".format(record_id)
        return ""

    record = ('<record><controlfield tag="001">{0}</controlfield>{1}'
              '</record>'.format(record_id, datafields))
    return record


def swap_clusters(linked_clusters):
    """Swap linked clusters.

    :param dict linked_clusters: contains the linked clusters
        created by the linking process. Keys are CDS profile ids to which the
        cluster belongs and values is a list containing `signature_id`s
        Example:
            {'2108556': ['1000048_Ellis, Jonathan Richard_3262364',
                         '100545_Ellis, Jonathan Richard_13778',
                         '1042975_John Ellis_3414782', ...],
             '2094406': ['2127658_Betti, Federico_8687791',
                         '5701_Betti, F_4574', ...],
             ...}

    :return: dictionary representing linked clusters in another format.
        Keys are CDS record ids which have to be updated and values is a list
        containing pairs. A pair contains the author's full name and its
        CDS profile id
        Example:
            {'1000048': {'Ellis, Jonathan Richard': '2108556'},
             '100545': {'Ellis, Jonathan Richard': '2108556'},
             '1042975': {'John Ellis': '2108556'},
             '2127658': {'Betti, Federico': '2094406'},
             '5701': {'Betti, F': '2094406'},
             ...}
    """
    clusters_swapped = {}
    for cds_id, signature_ids in linked_clusters.iteritems():
        for signature_id in signature_ids:
            signature_id_splitted = signature_id.split("_")
            publication_id = signature_id_splitted[0]
            author_name = signature_id_splitted[1]
            # TODO check for same author names in one record
            try:
                clusters_swapped[publication_id][author_name] = cds_id
            except KeyError:
                clusters_swapped[publication_id] = {author_name: cds_id}

    return clusters_swapped


def update(input_clusters, output_updates_dir, chunk_size=1000, upload=False):
    """Update authors which are linked to CDS profiles. 

    :param str input_clusters: file path to JSON file containing the
        linked clusters for updating the signatures
    :param str output_updates_dir: existing directory path to write XML files
        containing record updates used for bibupload
    :param int chunk_size: number of records to write to one file
    :param bool upload: send updates (`output_updates`) to bibupload if enabled
    """
    # Load linked clusters
    with open(input_clusters) as f:
        linked_clusters = load(f)
    print "{0} clusters have been loaded".format(len(linked_clusters))

    # Swap linked clusters
    clusters_swapped = swap_clusters(linked_clusters)
    print "{0} records to update".format(len(clusters_swapped))

    # Update records and write to (multiple) file(s)
    file_handle = None
    chunk = 0
    number_of_records = 0
    for cluster_id in clusters_swapped:
        if not number_of_records % chunk_size:
            if file_handle:
                file_handle.close()
            file_path = join(output_updates_dir,
                             "record_updates_{0}.xml".format(chunk))
            file_handle = open(file_path, "w")
            chunk += 1

        # cluster_id is representing the record id
        record_id = int(cluster_id)
        record = update_record(record_id, clusters_swapped[cluster_id])
        if record:
            file_handle.write(record)
            number_of_records += 1

    file_handle.close()

    # TODO upload: call bibupload (--correct), if file contains data and
    # `upload` is enabled

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_clusters", required=True, type=str,
                        help="Linked clusters by authority ids of signatures")
    parser.add_argument("--output_updates_dir", required=True, type=str,
                        help="Updates as MARC XML records used for bibupload")
    parser.add_argument("--chunk_size", default=1000, type=int,
                        help="Number of records to write to one file")
    parser.add_argument("--upload", default=0, type=int,
                        help="Whether it should be sent to bibupload or not")
    args = parser.parse_args()

    update(args.input_clusters, args.output_updates_dir,
           chunk_size = args.chunk_size, upload=args.upload == 1)

