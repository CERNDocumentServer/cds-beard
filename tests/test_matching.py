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

"""Test the matching algorithm."""

import json
import os
import unittest

from invenio_beard.matching import match_clusters

current_dir = os.path.dirname(__file__)


class TestMatching(unittest.TestCase):
    """Test different clusters."""

    def test_the_same_clusters(self):
        """Test if the two exact clusters will be matched."""

        signatures_before = {1: ['A', 'B']}
        signatures_after = {2: ['A', 'B']}

        match = match_clusters(signatures_before, signatures_after)

        self.assertEquals(match, ([(1, 2)], [], []))

    def test_cluster_adding(self):
        """Test if the new cluster will be distinguished."""

        partition_before = {}
        partition_after = {1: ['A', 'B']}

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([], [1], []))

    def test_cluster_removal(self):
        """Test if the removed cluster will be distinguished."""

        partition_before = {1: ['A', 'B']}
        partition_after = {}

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([], [], [1]))

    def test_complex_matching(self):
        """Test more complex clustering with no removal or adding."""

        partition_before = {1: ['A', 'B'], 2: ['C', 'D', 'E']}
        partition_after = {3: ['A', 'C', 'E'], 4: ['B', 'D']}

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 4), (2, 3)], [], []))

    def test_complex_adding(self):
        """Test more complex clustering with adding a new cluster."""

        partition_before = {1: ['A', 'B', 'C']}
        partition_after = {2: ['A', 'B'], 3: ['C']}

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 2)], [3], []))

    def test_complex_removal(self):
        """Test more complex clustering with removing a cluster."""

        partition_before = {1: ['A', 'B'], 2: ['C']}
        partition_after = {3: ['A', 'B', 'C']}

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 3)], [], [2]))

    def test_complex_subproblems(self):
        """Test the case, where there are at least two subproblems."""
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

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(4, 9), (1, 6), (2, 7), (3, 8)], [10], [5]))

    def test_wang_signtures(self):
        """Test the real output of Beard."""

        with open(os.path.join(
                current_dir, 'data/wang_clusters_1.json'), 'r') as file_before:
            signatures_before = json.load(file_before)

        match = match_clusters(signatures_before, signatures_before)

        self.assertEquals(match, ([(u'158992', u'158992'),
                                   (u'623639', u'623639'),
                                   (u'623638', u'623638')], [], []))

    def test_wang_signtures_mixed_up(self):
        """Test the real output of Beard."""

        with open(os.path.join(
                current_dir, 'data/wang_clusters_1.json'), 'r') as file_before:
            signatures_before = json.load(file_before)

        with open(os.path.join(
                current_dir, 'data/wang_clusters_2.json'), 'r') as file_after:
            signatures_after = json.load(file_after)

        match = match_clusters(signatures_before, signatures_after)

        self.assertEquals(match, ([(u'158992', u'158992'),
                                   (u'623639', u'623639')],
                                  [u'623638_to_add'], [u'623638']))

    def test_almost_the_same_keys(self):
        """Test the case where the keys are the same after casting."""
        partition_before = {1: ["A", "B", "C"],
                            "1": ["D", "E"]}

        partition_after = {1: ["A", "B", "C"],
                           "1": ["D", "E"]}

        match = match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([('1', '1'), (1, 1)], [], []))
