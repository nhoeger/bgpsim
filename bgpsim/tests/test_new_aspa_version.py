import random
import unittest
import sys
import os
from typing import List

import bgpsecsim.as_graph as as_graph
import bgpsecsim.experiments as experiments
from bgpsecsim.asys import AS, AS_ID, Relation, Route, RoutingPolicy
from bgpsecsim.as_graph import ASGraph
from bgpsecsim.routing_policy import (
    DefaultPolicy, RPKIPolicy, PathEndValidationPolicy,
    BGPsecHighSecPolicy, BGPsecMedSecPolicy, BGPsecLowSecPolicy,
    RouteLeakPolicy, ASPAPolicy, ASCONESPolicy, OnlyToCustomerPolicy
)
import bgpsecsim.experiments as experiments
import bgpsecsim.routing_policy as routing_policy

AS_REL_FILEPATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'as_aspa_otc.txt')


def test_relationships():
    nx_graph = as_graph.parse_as_rel_file(AS_REL_FILEPATH)
    graph = ASGraph(nx_graph)
    as1 = graph.get_asys("1")
    as2 = graph.get_asys("2")
    as3 = graph.get_asys("3")
    as4 = graph.get_asys("4")
    as5 = graph.get_asys("5")
    as666 = graph.get_asys("666")

    # Test relationships for AS 1
    assert as1.get_providers()[0] == "2"
    assert as1.neighbor_counts_by_relation()[Relation.PROVIDER] == 1
    assert as1.neighbor_counts_by_relation()[Relation.PEER] == 0
    assert as1.neighbor_counts_by_relation()[Relation.CUSTOMER] == 0

    # Test relationship for AS2
    assert as2.get_providers()[0] == "4"
    assert as2.get_customers()[0] == "1"
    assert as2.neighbor_counts_by_relation()[Relation.PROVIDER] == 1
    assert as2.neighbor_counts_by_relation()[Relation.PEER] == 0
    assert as2.neighbor_counts_by_relation()[Relation.CUSTOMER] == 1

    # Test relationship for AS3
    assert as3.get_providers()[0] == "4"
    assert as3.get_customers()[0] == "666"
    assert as3.get_customers()[1] == "5"
    assert as3.neighbor_counts_by_relation()[Relation.PROVIDER] == 1
    assert as3.neighbor_counts_by_relation()[Relation.PEER] == 0
    assert as3.neighbor_counts_by_relation()[Relation.CUSTOMER] == 2

    # Test relationship for AS4
    assert as4.get_customers()[0] == "2"
    assert as4.get_customers()[1] == "3"
    assert as4.get_customers()[2] == "666"
    assert as4.neighbor_counts_by_relation()[Relation.PROVIDER] == 0
    assert as4.neighbor_counts_by_relation()[Relation.PEER] == 0
    assert as4.neighbor_counts_by_relation()[Relation.CUSTOMER] == 3

    # Test relationship for AS5
    assert as5.get_providers()[0] == "3"
    assert as5.neighbor_counts_by_relation()[Relation.PROVIDER] == 1
    assert as5.neighbor_counts_by_relation()[Relation.PEER] == 0
    assert as5.neighbor_counts_by_relation()[Relation.CUSTOMER] == 0

    # Test relationship for AS666
    assert as666.get_providers()[0] == "4"
    assert as666.get_providers()[1] == "3"
    assert as666.neighbor_counts_by_relation()[Relation.PROVIDER] == 2
    assert as666.neighbor_counts_by_relation()[Relation.PEER] == 0
    assert as666.neighbor_counts_by_relation()[Relation.CUSTOMER] == 0


def new_success_rate(graph: ASGraph, attacker: AS, victim: AS) -> int:
    n_bad_routes = 0
    for asys in graph.asyss.values():
        route = asys.get_route(victim.as_id)
        print("Route: ", route)
        if route:
            offending_asys = leaked_route(route)
            print_string = str("Routes: " + str(route) + "; DO: " + str(route.local_data_part_do) + "; Bad Route: ")
            if offending_asys:
                print_string += offending_asys.as_id
                n_bad_routes += 1
                if offending_asys.as_id != attacker.as_id:
                    raise Exception("Attacker mismatches offending AS")
            else:
                print_string += "FALSE"

            # For debugging purpose: prints route + down only + bad route [False | Offending AS]
            print(print_string)

    return n_bad_routes


def leaked_route(route: ['Route']) -> AS:
    # Check for each AS except origin and destination in the path if Gao-Rexford was respected
    for idasys, asys in enumerate(route.path):
        if asys is not route.final and asys is not route.origin:
            previous_asys = route.path[idasys - 1]
            next_asys = route.path[idasys + 1]
            # Peer sends route to other peer or upstream
            if asys.get_relation(previous_asys) == Relation.PEER and (
                    asys.get_relation(next_asys) == Relation.PEER or asys.get_relation(next_asys) == Relation.PROVIDER):
                return asys  # return offending AS
            # Downstream sends route to other peer or upstream
            elif asys.get_relation(previous_asys) == Relation.PROVIDER and (
                    asys.get_relation(next_asys) == Relation.PEER or asys.get_relation(next_asys) == Relation.PROVIDER):
                return asys  # return offending AS
    return False


def prepare_policies():
    nx_graph = as_graph.parse_as_rel_file(AS_REL_FILEPATH)
    graph = ASGraph(nx_graph)
    as1 = graph.get_asys("1")
    as2 = graph.get_asys("2")
    as3 = graph.get_asys("3")
    as4 = graph.get_asys("4")
    as5 = graph.get_asys("5")
    as666 = graph.get_asys("666")

    all_as = graph.get_tierOne() + graph.get_tierTwo() + graph.get_tierThree()
    for elem in all_as:
        graph.get_asys(elem).policy = DefaultPolicy()
    as666.policy = RouteLeakPolicy()

    route_from_4 = Route(
        "4",
        [as1, as2],
        origin_invalid=False,
        path_end_invalid=False,
        authenticated=False,
        local_data_part_do="",
    )

    route_from_666 = Route(
        "666",
        [as1, as2],
        origin_invalid=False,
        path_end_invalid=False,
        authenticated=False,
        local_data_part_do="",
    )

    route_from_666_with_otc = Route(
        "666",
        [as1, as2],
        origin_invalid=False,
        path_end_invalid=False,
        authenticated=False,
        local_data_part_do="3",
    )

    as3.policy = OnlyToCustomerPolicy()

    print("AS666 Route:     ", as3.policy.accept_route(route_from_666))
    print("AS4 Route:       ", as3.policy.accept_route(route_from_4))
    print("AS666 OTC Route: ", as3.policy.accept_route(route_from_666_with_otc))
    print("Origin: ", route_from_666.path[0].as_id)

    as1.policy = ASPAPolicy()
    as3.policy = ASPAPolicy()
    as4.policy = ASPAPolicy()
    as1.create_new_aspa(graph)
    as3.create_new_aspa(graph)
    as4.create_new_aspa(graph)
    as3.policy = OnlyToCustomerPolicy()

    print("AS666 Route:     ", as3.policy.accept_route(route_from_666))
    print("AS4 Route:       ", as3.policy.accept_route(route_from_4))
    print("AS666 OTC Route: ", as3.policy.accept_route(route_from_666_with_otc))
    print("Origin: ", route_from_666.path[0].as_id)


class NewAspaVersionTest(unittest.TestCase):
    test_relationships()
    prepare_policies()
    pass


if __name__ == '__main__':
    unittest.main()
