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

import numpy as np

from scipy.optimize import linprog


def _cost_matrix(partition_before, partition_after):
    """Compute costs for the matching solver.

    Receives two partitions representing clusters in the state before
    and after running Beard algorithm. Each before-the-state-signature is
    being used to calculate the cost function against each of after-the-state-
    signatures. The cost function is calculating the overlap between
    members of the two given sets.

    :param partition_before:
        A dictionary of sets representing clusters of the signatures
        before running machine learning algorithm (Beard).

        Example:
            partition_before = {1: set(['A', 'B']), 2: set(['C'])}

    :param partition_after:
        A dictionary of sets representing clusters of the signatures
        after running machine learning algorithm (Beard).

        Example:
            partition_after = {3: set(['B']), 4: set(['A', 'C'])}

    :return:
        A matrix of (partition_before + partition_after) x (partition_after)
        size containing all costs values for each pair of clusters.

        Example:
            [[-1.25       -1.16666667]
             [-0.16666667 -1.25      ]
             [-0.25       -0.16666667]
             [-0.25       -0.16666667]]
    """

    cost = np.zeros((len(partition_before), len(partition_after)))

    # Keys in the dictionaries can be in any format.
    for index_before, cluster_before in enumerate(
                                            partition_before.viewvalues()):
        for index_after, cluster_after in enumerate(
                                            partition_after.viewvalues()):

            cost[index_before, index_after] = -len(
                set.intersection(
                    set(cluster_before), set(cluster_after))) - 1. / \
                (len(partition_after) * (1 + len(
                    set.symmetric_difference(set(cluster_before),
                                             set(cluster_after)))))

    return cost


def _match_clusters(partition_before, partition_after, maxiter=5000):
    """Solve the matching problem using simplex method.

    Receives a cost matrix produced by compute_cost_function_matrix.
    Using linprog method from scipy.optimize package, calculates
    the best match for each cluster from the-state-before with a
    cluster from the-state-after.

    :param partition_before:
        A dictionary of sets representing clusters of signatures
        before running machine learning algorithm (Beard).

        Example:
            partition_before = {1: set(['A', 'B']), 2: set(['C'])}

    :param partition_after:
        A dictionary of sets representing clusters of signatures
        after running machine learning algorithm (Beard).

        Example:
            partition_after = {3: set(['B']), 4: set(['A', 'C'])}

    :param maxiter:
        An optional parameter to define the maximum number of
        iterations to perform during linprog execution.

    :return:
        A tuple containing three buckets, representing **keys** of matched
        clusters (as pairs), new ones and removed.

        Example:
            ([(1, 2)], [3], [])
    """

    # Append virtual clusters (agents).
    for index in partition_after:
        partition_before['v' + str(index)] = set()

    # Compute the cost matrix.
    cost = _cost_matrix(partition_before,
                        partition_after)

    n_cluster_before, n_cluster_after = cost.shape
    n_edges = n_cluster_before * n_cluster_after

    # Each agent may be assigned to at most one task.
    A_ub = np.zeros((n_cluster_before, n_edges))

    for index in range(n_cluster_before):
        A_ub[index, index * n_cluster_after:(
            index + 1) * n_cluster_after] = 1.0

    b_ub = np.ones(n_cluster_before)

    # Each task has to be assignes to exactly one agent.
    A_eq = np.zeros((n_cluster_after, n_edges))

    for index in range(n_cluster_after):
        A_eq[index, index::n_cluster_after] = 1.0

    b_eq = np.ones(n_cluster_after)

    coefficients = cost.ravel()
    solution = linprog(coefficients,
                       A_ub=A_ub,
                       b_ub=b_ub,
                       A_eq=A_eq,
                       b_eq=b_eq,
                       options={'maxiter': maxiter})

    # Partition before-the-state has already appened agents.
    len_first = len(partition_before) - len(partition_after)
    len_second = len(partition_after)

    bucket_pairs = []
    bucket_new = []
    bucket_remove = []

    for index_first in range(len_first + len_second):
        for index_second in range(len_second):
            if solution.x[index_first * len_second + index_second] == 1:
                if index_first < len_first:
                    bucket_pairs.append((
                        partition_before.keys()[index_first],
                        partition_after.keys()[index_second]))
                else:
                    bucket_new.append(
                        partition_after.keys()[index_second])
                break
        else:
            if index_first < len_first:
                bucket_remove.append(
                    partition_before.keys()[index_first])

    return bucket_pairs, bucket_new, bucket_remove
