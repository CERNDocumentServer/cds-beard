"""Test cases for the updating module."""

import unittest

from updating import swap_clusters, update_record


class TestUpdating(unittest.TestCase):
    def test_update_record_main_author(self):
        """Test updating main author and creating MARC XML output."""
        result_expected = """<record><controlfield tag="001">2150939</controlfield>  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Ellis, John</subfield>
    <subfield code="u">King's Coll. London</subfield>
    <subfield code="u">CERN</subfield>
    <subfield code="0">AUTHOR|(CDS)2108556</subfield>
    <subfield code="9">#BEARD#</subfield>
  </datafield></record>"""

        result = update_record(2150939, {"Ellis, John": "2108556"})
        self.assertEqual(result, result_expected)

    def test_update_record_co_author(self):
        """Test updating co-author and creating MARC XML output."""
        result_expected = """<record><controlfield tag="001">2143998</controlfield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Fields, Brian D</subfield>
    <subfield code="u">Illinois U., Urbana, Astron. Dept.</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Ellis, John R</subfield>
    <subfield code="u">King's Coll. London</subfield>
    <subfield code="u">CERN</subfield>
    <subfield code="0">AUTHOR|(CDS)2108556</subfield>
    <subfield code="9">#BEARD#</subfield>
  </datafield></record>"""

        result = update_record(2143998, {"Ellis, John R": "2108556"})
        self.assertEqual(result, result_expected)

    def test_update_record_multiple_co_authors(self):
        """Test updating multiple co-authors and creating MARC XML output."""
        result_expected = """<record><controlfield tag="001">370253</controlfield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Lyons, K</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">McComb, T J L</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">McQueen, S</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Orford, K J</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Osborne, J L</subfield>
    <subfield code="0">AUTHOR|(CDS)2067465</subfield>
    <subfield code="9">#BEARD#</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Rayner, S M</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Shaw, S E</subfield>
    <subfield code="0">AUTHOR|(CDS)2089386</subfield>
    <subfield code="9">#BEARD#</subfield>
  </datafield>  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Turver, K E</subfield>
  </datafield></record>"""

        result = update_record(370253,
                               {"Osborne, J L": "2067465",
                                "Shaw, S E": "2089386"})
        self.assertEqual(result, result_expected)

    def test_update_record_empty(self):
        """Test creating MARC XML output for records having no updates."""
        test_records = [
            (2150939, {}),
            (2150939, {"Non-existing author": "123456"}),
            # Author already contains the same system control number
            (2153862, {"Marcastel, Fabienne": "2070305"})]
        result_expected = ""

        for record_id, authors in test_records:
            self.assertEqual(update_record(record_id, authors), result_expected)

    def test_swap_clusters(self):
        """Test swap clusters."""
        linked_clusters = {
            '2108556': ['1000048_Ellis, Jonathan Richard_3262364',
                        '100545_Ellis, Jonathan Richard_13778',
                        '1042975_John Ellis_3414782'],
            '2094406': ['2127658_Betti, Federico_8687791',
                        '5701_Betti, F_4574']}

        # Swapped linked clusters
        result_expected = {
            '1000048': {'Ellis, Jonathan Richard': '2108556'},
            '100545': {'Ellis, Jonathan Richard': '2108556'},
            '1042975': {'John Ellis': '2108556'},
            '2127658': {'Betti, Federico': '2094406'},
            '5701': {'Betti, F': '2094406'}}

        self.assertEqual(swap_clusters(linked_clusters), result_expected)

if __name__ == '__main__':
    unittest.main()

