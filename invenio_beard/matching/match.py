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

from .simplex import _match_clusters

from .subproblems import _divide_into_subproblems


def do_matching(signatures_before, signatures_after):
    """Split the given signatures into subproblems, then match.

    Receives two dictionaries, representing clustered signatures
    before and after running the machine learning algorithm (Beard).
    The signatures_before are clustered by authors pointing to the same
    profile, where signatures_after is clustered by Beard.
    The keys in the given dictionaries must be different.

    :param signatures_before:
        A dictionary containing clusterd signatures by the same profile.

        Example:
            signatures_before = {"1": ["A"], "2": ["B"], "3": ["C"]}

    :param signatures_after:
        A dictionary, which is an output of Beard.

        Example:
            signatures_after = {"4": ["A"], "5": ["B"], "6": ["D"]}

    :return:
        The method returns three buckets (lists) containing the keys of matched
        clusters (as pairs), new clusters and these to remove.

        Example:
            ([(1, 4), (2, 5)], [6], [3])
    """

    bucket_matched = []
    bucket_new = []
    bucket_removed = []

    for subproblem_before, subproblem_after in _divide_into_subproblems(
                                                    signatures_before,
                                                    signatures_after):

        matching_result = _match_clusters(subproblem_before,
                                          subproblem_after)

        if matching_result[0]:
            bucket_matched.append(matching_result[0])

        if matching_result[1]:
            bucket_new.append(matching_result[1])

        if matching_result[2]:
            bucket_removed.append(matching_result[2])

    return bucket_matched, bucket_new, bucket_removed
