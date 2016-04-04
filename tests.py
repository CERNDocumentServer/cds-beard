"""Test cases for the clustering and querying module.

All test cases are based on cds-test data.
"""

import unittest

from clustering import block_clustering

from querying import (
    create_record, create_signature_block, create_signatures, get_record_ids)


class TestQuerying(unittest.TestCase): 
    def test_create_record(self):
        """Test creating records."""
        # Test regular record
        record = create_record(123456)
        self.assertEqual(record["publication_id"], "123456")
        self.assertEqual(record["authors"], ["Frazer, W R", "Gunion, J F"])
        self.assertEqual(record["year"], "1980")
        self.assertEqual(record["title"], "Target mass corrections in QCD")
        self.assertEqual(record["collaboration"], False)
        
        # Test record containing a range as year, e.g. 1958-1960
        record = create_record(223456)
        self.assertEqual(record["year"], "1958")
        
        # Test record containing list of years (multiple 260__c fields)
        record = create_record(99987)
        self.assertEqual(record["year"], "1981")

        # Test existing (not marked as deleted), but invalid record
        record = create_record(12345)
        self.assertEqual(record, None)

        # Test record which is part of a collaboration only
        record = create_record(1967508)
        self.assertEqual(record, None)

        # Test record which is part of a "colaboration" only
        record = create_record(2019849)
        self.assertEqual(record, None)

        # Test record which is part of a collaboration and contains "real" author
        record = create_record(1255874)
        self.assertEqual(record["publication_id"], "1255874")
        self.assertEqual(
            record["authors"], ["ATLAS Collaboration", "Joao Pequenao"]) 
        self.assertEqual(record["collaboration"], True)

        # Test non-existing record
        record = create_record(0)
        self.assertEqual(record, None)

    def test_create_signatures(self):
        """Test creating signatures."""
        # Test signature containing author without affiliation
        signatures = create_signatures(123456)
        self.assertEqual(len(signatures), 2)
        self.assertEqual(signatures[0]["signature_id"], "123456_Frazer, W R")
        self.assertEqual(signatures[0]["publication_id"], "123456")
        self.assertEqual(signatures[0]["author_name"], "Frazer, W R")
        self.assertEqual(signatures[0]["author_affiliation"], "")
        
        self.assertEqual(signatures[1]["signature_id"], "123456_Gunion, J F")
        self.assertEqual(signatures[1]["publication_id"], "123456")
        self.assertEqual(signatures[1]["author_name"], "Gunion, J F")
        self.assertEqual(signatures[1]["author_affiliation"], "")

        # Test signature containing author with affiliation
        signatures = create_signatures(45895)
        self.assertEqual(signatures[0]["author_affiliation"], "CERN")

        # Test signature containing author with two affiliations
        signatures = create_signatures(46183)
        self.assertEqual(signatures[0]["author_affiliation"],
                         "CERN the US National Science Foundation")

        # Test signature containing a collaboration
        signatures = create_signatures(1967508)
        self.assertEqual(signatures, [])

    # @unittest.skip("skippy the skipper")
    def test_get_record_ids(self):
        """Test fetching public bibliographic record-ids from CDS."""
        record_ids = get_record_ids()
        
        # Test non-empty record list
        self.assertTrue(record_ids)

        # Test valid record
        record_in_list = 1369415 in record_ids
        self.assertTrue(record_in_list)

        # Test deleted record
        record_not_in_list = 1 in record_ids
        self.assertFalse(record_not_in_list)

        # Test invalid record
        record_not_in_list = 12345 in record_ids
        self.assertFalse(record_not_in_list)

        # Test authority record
        record_not_in_list = 2108556 in record_ids
        self.assertFalse(record_not_in_list)

    def test_clustering(self):
        """Test pre-clustering records and signatures by phonetic blocks.
        
        Phonetic blocks are created given the  author's full name. Example: the 
        phonetic block of the name "Ellis, J" is "ELj". The same for
        "Ellis, John", "Ellis, Jonathan Richard", and "Ellis, John R". That
        said, all records and signatures containing this author's full name,
        have to be in the same cluster.

        This test case pre-clusters 4 records and its containing signatures (9)
        into 6 clusters. Every record contains an author with one of the
        mentioned name variation.

        Records (ids, author's full names, and phonetic block:
            1369415:
                Ellis, J ("ELj");
                McLaughlin, M A ("MCLAGHLANm");
                Verbiest, J P W ("VARBASTj")
            1638463:
                Ellis, John ("ELj")
            1112288:
                Ellis, Jonathan Richard ("ELj")
            1181000:
                Butterworth, Jonathan M ("BATARWARTHj");
                Ellis, John R ("ELj");
                Raklev, Are R ("RACLAFa");
                Salam, Gavin P ("SALANg")
        """
        record_ids = [1369415, 1638463, 1112288, 1181000]
        records_by_blocks, signatures_by_blocks = block_clustering(record_ids)

        # Test number of clusters (phonetic blocks)
        self.assertEqual(len(signatures_by_blocks.keys()), 6)
        self.assertEqual(len(records_by_blocks.keys()), 6)

        # Test number of records for each cluster
        self.assertEqual(len(records_by_blocks["ELj"]), 4)
        self.assertEqual(len(records_by_blocks["MCLAGHLANm"]), 1)
        self.assertEqual(len(records_by_blocks["VARBASTj"]), 1)
        self.assertEqual(len(records_by_blocks["BATARWARTHj"]), 1)
        self.assertEqual(len(records_by_blocks["RACLAFa"]), 1)
        self.assertEqual(len(records_by_blocks["SALANg"]), 1)

        # Test number of signatures for each cluster
        self.assertEqual(len(signatures_by_blocks["ELj"]), 4)
        self.assertEqual(len(signatures_by_blocks["MCLAGHLANm"]), 1)
        self.assertEqual(len(signatures_by_blocks["VARBASTj"]), 1)
        self.assertEqual(len(signatures_by_blocks["BATARWARTHj"]), 1)
        self.assertEqual(len(signatures_by_blocks["RACLAFa"]), 1)
        self.assertEqual(len(signatures_by_blocks["SALANg"]), 1)
               
        # Test record-ids in cluster "ELj"
        ELj_record_ids = [
            int(rec["publication_id"]) for rec in records_by_blocks["ELj"]]
        self.assertEqual(set(ELj_record_ids), set(record_ids))
        
        # Test record-id in cluster "MCLAGHLANm"
        self.assertEqual(
            records_by_blocks["MCLAGHLANm"][0]["publication_id"], "1369415")

        # Test author_name for signature in cluster "MCLAGHLANm"
        self.assertEqual(
            signatures_by_blocks["MCLAGHLANm"][0]["author_name"],
            "McLaughlin, M A")

        record_ids = [2011342]
        records_by_blocks, signatures_by_blocks = block_clustering(record_ids)

        # Test cluster "WANGl"
        # Record contains two signatures with the same phonetic block "WANGl"
        self.assertEqual(len(records_by_blocks["WANGl"]), 1)
        self.assertEqual(len(signatures_by_blocks["WANGl"]), 2)

if __name__ == '__main__':
    unittest.main()

