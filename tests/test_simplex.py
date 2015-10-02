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

"""Test the simplex algorithm."""

import unittest

from invenio_beard.matching.simplex import _match_clusters


class TestSimplex(unittest.TestCase):
    """Test different clusters."""

    def test_the_same_clusters(self):
        """Test if the two exact clusters will be matched."""

        partition_before = {1: set(['A', 'B'])}
        partition_after = {2: set(['A', 'B'])}

        match = _match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 2)], [], []))

    def test_cluster_adding(self):
        """Test if the new cluster will be distinguished."""

        partition_before = {}
        partition_after = {1: set(['A', 'B'])}

        match = _match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([], [1], []))

    def test_cluster_removal(self):
        """Test if the removed cluster will be distinguished."""

        partition_before = {1: set(['A', 'B'])}
        partition_after = {}

        match = _match_clusters(partition_before,
                                partition_after)

        self.assertEquals(match, ([], [], [1]))

    def test_complex_matching(self):
        """Test more complex clustering with no removal or adding."""

        partition_before = {1: set(['A', 'B']), 2: set(['C', 'D', 'E'])}
        partition_after = {3: set(['A', 'C', 'E']), 4: set(['B', 'D'])}

        match = _match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 4), (2, 3)], [], []))

    def test_complex_adding(self):
        """Test more complex clustering with adding a new cluster."""

        partition_before = {1: set(['A', 'B', 'C'])}
        partition_after = {2: set(['A', 'B']), 3: set(['C'])}

        match = _match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 2)], [3], []))

    def test_complex_removal(self):
        """Test more complex clustering with removing a cluster."""

        partition_before = {1: set(['A', 'B']), 2: set(['C'])}
        partition_after = {3: set(['A', 'B', 'C'])}

        match = _match_clusters(partition_before, partition_after)

        self.assertEquals(match, ([(1, 3)], [], [2]))
