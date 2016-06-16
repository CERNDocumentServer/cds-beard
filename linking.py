"""Linking module to link signatures of predicted clusters to authority records.
"""

import argparse

from json import load, dump


def clusters_having_authority_ids(predicted_clusters, signatures):
    """Get predicted clusters having signatures with authority ids.
    
    Such predicted clusers are considered for linking only.

    :param dict predicted_clusters: predicted clusters from clustering

    :return: list of all clusters having signatures with authority ids
    """
    predicted_clusters_having_ids = []
    for cluster in predicted_clusters:
        for signature_id in predicted_clusters[cluster]:
            signature = signatures[signature_id]
            if (signature.get("author_cds_id") or
                signature.get("author_cern_id") or
                signature.get("author_inspire_id")):
                predicted_clusters_having_ids.append(cluster)
                break
    return predicted_clusters_having_ids


def group_by_authority_id(predicted_cluster, signatures):
    """Group together signatures by their authority ids and `rest`.
    
    Giving a predicted cluster, representing a list of signature ids,
    group together all signatures having the same authority id, and
    the `rest` (signatures having no authority id).
    
    Signatures having several authority ids, will be grouped into different
    groups.

    :param list predicted_cluster: group of signature ids of predicted cluster

    :return: pair containing a dictionary representing the grouped signatures
        by authority ids and a list representing signature ids having no
        authorit id
    """
    grouped_signatures = {}
    rest = []  # List of signature ids having no authority id
    
    for signature_id in predicted_cluster:
        signature = signatures[signature_id]
        
        # In the current set of signatures, authority ids can be an empty string
        cds_id = signature.get("author_cds_id")
        cern_id = signature.get("author_cern_id")
        inspire_id = signature.get("author_inspire_id")
        
        if cds_id:
            cds_authority_id = "AUTHOR|(CDS){}".format(cds_id)
            try:
                grouped_signatures[cds_authority_id].append(signature_id)
            except KeyError:
                grouped_signatures[cds_authority_id] = [signature_id]

        if cern_id:
            cern_authority_id = "AUTHOR|(SzGeCERN){}".format(cern_id)
            try:
                grouped_signatures[cern_authority_id].append(signature_id)
            except KeyError:
                grouped_signatures[cern_authority_id] = [signature_id]

        if inspire_id:
            inspire_authority_id = "AUTHOR|(INSPIRE)INSPIRE-{}".format(inspire_id)
            try:
                grouped_signatures[inspire_authority_id].append(signature_id)
            except KeyError:
                grouped_signatures[inspire_authority_id] = [signature_id]
                
        if not (cds_id or cern_id or inspire_id):
            rest.append(signature_id)
                
    return (grouped_signatures, rest)
 

def single_matching(signature_id, linked_signatures, signatures):
    """Try matching a signature having no authority id.
    
    Find a match for a signature in linked signatures, by applying
    simple string matching on the signature's author full name to
    check if linked signatures contains a signature having the same name.
    
    :param str signature_id: signature id to be matched
    :param list linked_signatures: list of signature ids which have been
        matched already
    
    :return: True, if signature could be matched to a signature in
        linked signatures, False otherwise.
    """
    author_name = signatures[signature_id]["author_name"]
    if any(author_name == signatures[id_]["author_name"] for
           id_ in linked_signatures):
        return True
    return False


def link_cluster(predicted_cluster, signatures, lookup, mode="fair"):
    """Link signatures of predicted cluster to author profile.
    
    Signatures of a predicted cluster are grouped together by the
    same authority id, and then linked by applying a linking function
    based on different modes.
    
     single matching: link single signatures (of a group or `rest`) only
     group matching: link all signatures in the same group
        
    :param list predicted_cluster: list of signature ids of a predicted cluster
    :param str mode: applies the given mode for matching signatures.
        pessimistic: link groups of signatures having a perfect match only
        careful: (pessimistic) + single matching
        fair: (pessimistic) + group matching
        adventurous: link full predicted cluster once one signature can be linked
    """
    # Return as pair
    record_id = None  # Referencing to the author profile page
    # Signature ids belonging to the same author
    linked_signatures = [] 
    
    grouped_signatures, rest = group_by_authority_id(predicted_cluster,
                                                     signatures)
    
    # Sort grouped signatures by number of signatures each group;
    # descending order
    grouped_signatures_sorted = sorted(grouped_signatures,
                                       key=lambda k: len(grouped_signatures[k]),
                                       reverse=True)

    # Step 1: Find record id of the largest group,
    # and link in case of a match
    for authority_id in grouped_signatures_sorted:
        try:
            # Look-up record id of the author profile
            record_id = lookup[authority_id]
            linked_signatures.extend(grouped_signatures[authority_id])
            # Remove group from list
            grouped_signatures_sorted.remove(authority_id)
            break
        except KeyError:
            # No authority record id has been found for this signature group
            pass
        
    if not record_id:
        # Couldn't find a matching record id for predicted_cluster
        return (record_id, linked_signatures)
    
    if mode == "adventurous":
        return (record_id, predicted_cluster)
    
    # Step 2: Match all other groups, if any
    for authority_id in grouped_signatures_sorted:
        try:
            cds_id = lookup[authority_id]  # Authority record id 
            if record_id == cds_id:
                # Perfect match: same ids
                linked_signatures.extend(grouped_signatures[authority_id])
            else:
                # Wrong match: group of signatures belong to a
                # differnt authority record id than the one being matched
                pass
        except KeyError:
            # No authority record id has been found for this signature group
            if mode == "careful":
                # Single signature matching
                for signature_id in grouped_signatures[authority_id]:
                    # Signature could be already matched, e.g. if in 
                    # several groups due to >1 authority ids
                    if (signature_id not in linked_signatures and
                        single_matching(signature_id,
                                        linked_signatures,
                                        signatures)):
                        linked_signatures.append(signature_id)
            elif mode == "fair":
                # Group matching
                linked_signatures.extend(grouped_signatures[authority_id])
            
    # Step 3: Match `rest` (signatures having no authority id)
    if mode == "careful" or mode == "fair":
        for signature_id in rest:
            if single_matching(signature_id, linked_signatures, signatures):
                linked_signatures.append(signature_id)

    # Remove duplicates
    linked_signatures = list(set(linked_signatures))
    return (record_id, linked_signatures)


def linking(input_clusters, input_signatures, input_lookup, output_clusters,
            mode, silent=False):
    """Link signatures of predicted clusters to CDS profiles.
    
    :param str input_clusters: file path to the predicted clusters created by
        Beard
    :param str input_signatures: file path to signatures representing CDS
        meta data of an author
    :param str input_lookup: file path to the JSON file containing the look-up
        for CDS profile ids by giving a authority id
    :param str output_clusters: file path to the output JSON file storing
        the linked clusters
    :param str mode:
    """
    # Load signatures
    with open(input_signatures) as f:
        signatures = load(f)
    print "{0} signatures have been loaded".format(len(signatures))

    if isinstance(signatures, list):
        signatures = {s["signature_id"]: s for s in signatures}

    # Load predicted clusters
    with open(input_clusters) as f:
        predicted_clusters = load(f)
    print "{0} predicted clusters have been loaded".format(
        len(predicted_clusters))
   
    # List of predicted clusters having signatures with authority ids
    predicted_clusters_to_link = clusters_having_authority_ids(
        predicted_clusters, signatures)
    print "{0} predicted clusters have been selected for linking".format(
        len(predicted_clusters_to_link))

    # Load look-up 
    with open(input_lookup) as f:
        lookup = load(f)
    print "{0} authority ids have been loaded".format(len(lookup))

    linked_clusters = {}
    for cluster in predicted_clusters_to_link:
        record_id, linked_signatures = link_cluster(
            predicted_clusters[cluster], signatures, lookup, mode)
        linked_clusters[record_id] = linked_signatures

        if not silent:
            # Terminal output:
            print ("Predicted cluster '{0}': record id: '{1}', "
                   "linked signatures: {2}/{3}").format(
                       cluster, record_id, len(linked_signatures),
                       len(predicted_clusters[cluster]))

    with open(output_clusters, "w") as f:
        dump(linked_clusters, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_clusters", required=True, type=str,
                        help="Predicted clusters created by Beard")
    parser.add_argument("--input_signatures", required=True, type=str,
                        help="Signatures representing an author's meta data")
    parser.add_argument("--input_lookup", required=True, type=str,
                        help="Look-up for profile ids for given authority ids")
    parser.add_argument("--output_clusters", required=True, type=str,
                        help="Linked clusters by CDS profiles")
    parser.add_argument("--mode", default="fair", type=str,
                        help=("Mode used for linking: `pessimistic`, "
                              "`careful`, `fair`, or `adventurous`"))
    parser.add_argument("--silent", default=0, type=int,
                        help="Whether the results are printed or not")

    args = parser.parse_args()

    linking(args.input_clusters, args.input_signatures, args.input_lookup,
            args.output_clusters, args.mode, args.silent == 1)

