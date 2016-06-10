"""Test cases for the querying module."""

import unittest

from itertools import count

class TestRecords(unittest.TestCase):

    """Test cases for `create_record`."""

    def test_create_record(self):
        """Test creating record."""
        from querying import create_record

        test_records = [
            # `100` field
            (987329, {'publication_id': '987329',
                      'title': 'Search for Supersymmetry',
                      'year': '2006',
                      'authors': ['Ellis, Jonathan Richard']}),
            # `100` and `700` field
            (123456, {'publication_id': '123456',
                      'title': 'Target mass corrections in QCD',
                      'year': '1980',
                      'authors': ['Frazer, W R', 'Gunion, J F']}),
            # `100` and two `700` fields
            (223456, {'publication_id': '223456',
                      'title': ('Frans woordenboek Frans-Nederlands, '
                                'Nederlands-Frans'),
                      'year': '1958',  # 1958-1960
                      'authors': ['Herckenrath, C R C',
                                  'Boulan, H R', 'Dory, Albert']}),
            (99987, {'publication_id': '99987',
                     'title': 'Physical kinetics',
                     'year': '1981',  # multiple `260__c` fields
                     'authors': ['Lifshitz, Evgenii Mikhailovich',
                                 'Pitaevskii, Lev Petrovich']})
        ]

        for test_record in test_records:
            record_id, record_expected = test_record
            self.assertEqual(create_record(record_id), record_expected)

    def test_create_record_none(self):
        """Test creating record having no `real` authors."""
        from querying import create_record

        test_records = [
            # No `100` or `700` fields
            (12345, None),
            # Collaboration only
            (1967508, None),
            (2019849, None)
        ]

        for test_record in test_records:
            record_id, record_expected = test_record
            self.assertEqual(create_record(record_id), record_expected)

    def test_create_record_collaboration(self):
        """Test creating record contributed also by collaborations."""
        from querying import create_record

        test_records = [
            # Collaboration and `real` author
            (1255874, {'publication_id': '1255874',
                       'title': ('ATLAS animation of real event displays at '
                                 '7 TeV on March 30th'),
                       'year': '2010',
                       'authors': ['Joao Pequenao']})
        ]

        for test_record in test_records:
            record_id, record_expected = test_record
            self.assertEqual(create_record(record_id), record_expected)

class TestSignatures(unittest.TestCase):

    """Test cases for `create_signatures`."""

    def test_create_signatures(self):
        """Test creating signatures."""
        import querying
        querying.consecutive_id = count()

        signatures = querying.create_signatures(123456)
        signatures_expected = [
            {'publication_id': '123456',
             'signature_id': '123456_Frazer, W R_0',
             'author_affiliation': '',
             'author_name': 'Frazer, W R'},
            {'publication_id': '123456',
             'signature_id': '123456_Gunion, J F_1',
             'author_affiliation': '',
             'author_name': 'Gunion, J F'}]
        self.assertEqual(signatures, signatures_expected)

    def test_create_signatures_affiliation(self):
        """Test creating signatures."""
        import querying
        querying.consecutive_id = count()

        test_signatures = [
            # One affiliation
            (139935, [{'publication_id': '139935',
                       'signature_id': '139935_Ellis, Jonathan Richard_0',
                       'author_affiliation': 'CERN',
                       'author_name': 'Ellis, Jonathan Richard'},
                      {'publication_id': '139935',
                       'signature_id': '139935_Hagelin, John S_1',
                       'author_affiliation': '',
                       'author_name': 'Hagelin, John S'}]),
            # Multiple affiliations
            (2143438, [{'publication_id': '2143438',
                        'signature_id': '2143438_Ellis, John_2',
                        'author_affiliation': "CERN King's Coll. London",
                        'author_name': 'Ellis, John'}])
        ]

        for test_signature in test_signatures:
            record_id, signatures_expected = test_signature
            self.assertEqual(
                querying.create_signatures(record_id), signatures_expected)

    def test_create_signatures_empty(self):
        """Test creating signatures of collaborations."""
        from querying import create_signatures

        test_signatures = [
            (1967508, [])
        ]

        for test_signature in test_signatures:
            record_id, signatures_expected = test_signature
            self.assertEqual(create_signatures(record_id), signatures_expected)

    def test_create_signatures_authority_ids(self):
        """Test creating signatures having authority ids."""
        import querying
        querying.consecutive_id = count()

        test_signatures = [
            # 700__i: INSPIRE-00172591
            # 700__j: CCID-640877
            (2151783, [{'publication_id': '2151783',
                        'author_name': 'Ciesielski, Robert Adam',
                        'signature_id': '2151783_Ciesielski, Robert Adam_0',
                        'author_affiliation': 'Rockefeller U.',
                        'author_cern_id': '640877',
                        'author_inspire_id': '00172591'}]),
            # 100__0: AUTHOR|(CDS)2075804
            # 100__0: AUTHOR|(SzGeCERN)679148
            (2124613, [{'author_cds_id': '2075804',
                        'publication_id': '2124613',
                        'author_cern_id': '679148',
                        'author_name': 'Ukleja, Artur',
                        'signature_id': '2124613_Ukleja, Artur_1',
                        'author_affiliation': ('National Centre for Nuclear '
                                               'Research (PL)')}]),
            # 700__i: INSPIRE-00124113
            # 700__j: CCID-455276
            (1446555, [{'publication_id': '1446555',
                        'signature_id': '1446555_Bechtel, Florian_2',
                        'author_affiliation': 'Hamburg U.',
                        'author_cern_id': '627870',
                        'author_name': 'Bechtel, Florian'},
                       {'publication_id': '1446555',
                        'author_cern_id': '455276',
                        'author_inspire_id': '00124113',
                        'author_name': 'Schleper, Peter',
                        'signature_id': '1446555_Schleper, Peter_3',
                        'author_affiliation': 'Hamburg U.'}]),
            # 100__0: AUTHOR|(SzGeCERN)678846
            # 100__i: INSPIRE-00374510
            # 100__j: CCID-678846
            (2050951, [{'publication_id': '2050951',
                        'author_cern_id': '678846',
                        'author_inspire_id': '00374510',
                        'author_name': 'Martin, Christopher Blake',
                        'signature_id': '2050951_Martin, Christopher Blake_4',
                        'author_affiliation': 'Johns Hopkins U.'},
                       {'publication_id': '2050951',
                        'author_cern_id': '654418',
                        'author_inspire_id': '00086850',
                        'author_name': 'Gritsan, Andrei',
                        'signature_id': '2050951_Gritsan, Andrei_5',
                        'author_affiliation': 'Johns Hopkins U.'}])
        ]

        for test_signature in test_signatures:
            record_id, signatures_expected = test_signature
            self.assertEqual(
                querying.create_signatures(record_id), signatures_expected)

class TestRecordAndSignatures(unittest.TestCase):

    """Test cases for creating signatures and record using same record object.

    Request the CDS record only once and pass it to `create_signatures` and
    `create_record`.
    """

    def test_create_record_and_signatures(self):
        """Test creating record and signatures."""
        import querying
        from invenio.search_engine import get_record
        querying.consecutive_id = count()

        record_id = 123456
        cds_record = get_record(record_id)
        signatures = querying.create_signatures(record_id, cds_record)
        record = querying.create_record(record_id, cds_record)

        record_expected = {
            'publication_id': '123456',
            'title': 'Target mass corrections in QCD',
            'year': '1980',
            'authors': ['Frazer, W R', 'Gunion, J F']}

        signatures_expected = [
            {'publication_id': '123456',
             'signature_id': '123456_Frazer, W R_0',
             'author_affiliation': '',
             'author_name': 'Frazer, W R'},
            {'publication_id': '123456',
             'signature_id': '123456_Gunion, J F_1',
             'author_affiliation': '',
             'author_name': 'Gunion, J F'}]

        self.assertEqual(signatures, signatures_expected)
        self.assertEqual(record, record_expected)


class TestAuthorityIds(unittest.TestCase):

    """Test `get_authority_ids` for a given `author` object.

    Example:
        from invenio.search_engine import get_record
        record = get_record(<record id>)
        author = record["100"][0]  # or for `700` fields
    """

    def test_authority_ids(self):
        """Test valid authority ids, case insensitive."""
        from querying import get_authority_ids

        author = ([('j', 'CDS-333'),
                   ('i', 'inspire-222'),
                   ('0', 'CCID-111')], ' ', ' ', '', 1)
        authority_ids_expected = {
            "cern_id": "111", "inspire_id": "222", "cds_id": "333"}

        self.assertEqual(get_authority_ids(author), authority_ids_expected)

    def test_authority_ids_cern(self):
        """Test CERN authority ids."""
        from querying import get_authority_ids

        authors = [
            ([('0', 'CERN-123')], ' ', ' ', '', 1),
            ([('0', 'CCID-123')], ' ', ' ', '', 1),
            ([('0', 'AUTHOR|(SzGeCERN)123')], ' ', ' ', '', 1),
            ([('h', 'CERN-123')], ' ', ' ', '', 1),
            ([('h', 'CCID-123')], ' ', ' ', '', 1),
            ([('h', 'AUTHOR|(SzGeCERN)123')], ' ', ' ', '', 1),
            ([('i', 'CERN-123')], ' ', ' ', '', 1),
            ([('i', 'CCID-123')], ' ', ' ', '', 1),
            ([('i', 'AUTHOR|(SzGeCERN)123')], ' ', ' ', '', 1),
            ([('j', 'CERN-123')], ' ', ' ', '', 1),
            ([('j', 'CCID-123')], ' ', ' ', '', 1),
            ([('j', 'AUTHOR|(SzGeCERN)123')], ' ', ' ', '', 1)
        ]
        authority_ids_expected = {"cern_id": "123"}

        for author in authors:
            self.assertEqual(get_authority_ids(author), authority_ids_expected)

    def test_authority_ids_inspire(self):
        """Test INSPIRE authority ids."""
        from querying import get_authority_ids

        authors = [
            ([('0', 'INSPIRE-123')], ' ', ' ', '', 1),
            ([('0', 'AUTHOR|(INSPIRE)INSPIRE-123')], ' ', ' ', '', 1),
            ([('h', 'INSPIRE-123')], ' ', ' ', '', 1),
            ([('h', 'AUTHOR|(INSPIRE)INSPIRE-123')], ' ', ' ', '', 1),
            ([('i', 'INSPIRE-123')], ' ', ' ', '', 1),
            ([('i', 'AUTHOR|(INSPIRE)INSPIRE-123')], ' ', ' ', '', 1),
            ([('j', 'INSPIRE-123')], ' ', ' ', '', 1),
            ([('j', 'AUTHOR|(INSPIRE)INSPIRE-123')], ' ', ' ', '', 1)
        ]
        authority_ids_expected = {"inspire_id": "123"}

        for author in authors:
            self.assertEqual(get_authority_ids(author), authority_ids_expected)

    def test_authority_ids_cds(self):
        """Test CDS authority ids."""
        from querying import get_authority_ids

        authors = [
            ([('0', 'CDS-123')], ' ', ' ', '', 1),
            ([('0', 'AUTHOR|(CDS)123')], ' ', ' ', '', 1),
            ([('h', 'CDS-123')], ' ', ' ', '', 1),
            ([('h', 'AUTHOR|(CDS)123')], ' ', ' ', '', 1),
            ([('i', 'CDS-123')], ' ', ' ', '', 1),
            ([('i', 'AUTHOR|(CDS)123')], ' ', ' ', '', 1),
            ([('j', 'CDS-123')], ' ', ' ', '', 1),
            ([('j', 'AUTHOR|(CDS)123')], ' ', ' ', '', 1)
        ]
        authority_ids_expected = {"cds_id": "123"}

        for author in authors:
            self.assertEqual(get_authority_ids(author), authority_ids_expected)

    def test_authority_ids_none(self):
        """Test `author` objects by expecting empty dictionary."""
        from querying import get_authority_ids

        authors = [
            ([('0', 'CERN12345')], ' ', ' ', '', 1),
            ([('i', 'inspire')], ' ', ' ', '', 1),
            ([('u', 'INSPIRE-123')], ' ', ' ', '', 1),
            ([('0', 'INSPIRE-')], ' ', ' ', '', 1),
            ([('0', 'CERN-')], ' ', ' ', '', 1),
            ([('0', 'CCID--1')], ' ', ' ', '', 1)
        ]
        authority_ids_expected = {}

        for author in authors:
            self.assertEqual(get_authority_ids(author), authority_ids_expected)

if __name__ == '__main__':
    unittest.main()

