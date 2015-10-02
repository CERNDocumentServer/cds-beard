# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test the dividing algorithm."""

import unittest

from invenio_beard.matching.subproblems import _divide_into_subproblems


class TestSubproblems(unittest.TestCase):
    """Test the splitting on given sets into subsets with common members."""

    def test_splitting(self):
        """Test if the method splits correctly."""
        partition_before = {1: ["A", "B", "C"],
                            2: ["D", "E"],
                            3: ["F"],
                            4: ["G"],
                            5: ["H"]}

        partition_after = {6: ["A", "B"],
                           7: ["C", "D"],
                           8: ["E", "F"],
                           9: ["G"],
                           10: ["I"]}

        match = _divide_into_subproblems(partition_before, partition_after)
        exprected_match = [({1: set(['A', 'B', 'C']), 2: set(['D', 'E']),
                             3: set(['F'])},
                            {6: set(['A', 'B']), 7: set(['C', 'D']),
                             8: set(['E', 'F'])}),
                           ({4: set(['G'])}, {9: set(['G'])}),
                           ({5: set(['H'])}, {}),
                           ({}, {10: set(['I'])})]

        self.assertEquals(match, exprected_match)

    def test_empty_value(self):
        """Test if the method passes empty values correctly."""
        partition_before = {1: ["A", "B", "C"],
                            2: []}

        partition_after = {3: ["A", "B"],
                           4: ["C", "D"]}

        match = _divide_into_subproblems(partition_before, partition_after)
        exprected_match = [({1: set(['A', 'B', 'C'])},
                            {3: set(['A', 'B']), 4: set(['C', 'D'])}),
                           ({2: set()}, {})]

        self.assertEquals(match, exprected_match)

    def test_type_error(self):
        """Test if the method fails on values with no len() attribute."""
        partition_before = {1: 42}

        partition_after = {}

        with self.assertRaises(TypeError):
            _divide_into_subproblems(partition_before, partition_after)
