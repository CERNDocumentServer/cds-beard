"""Test cases for the clustering module.

Requires Beard installation.
"""

import unittest

from clustering import block_clustering

from invenio.search_engine import get_record


class TestClustering(unittest.TestCase): 

    """Test cases for block clustering."""

    def test_clustering(self):
        """Test pre-clustering records and signatures by phonetic blocks.

        Phonetic blocks are created of the givenauthor's full name.
        Example: the phonetic block of the name "Ellis, J" is "ELj". The same
        for "Ellis, John", "Ellis, Jonathan Richard", and "Ellis, John R". That
        being said, all records and signatures containing this author's full
        name, have to be in the same phonetic cluster.

        This test case pre-clusters 4 records and its containing 9 signatures
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

