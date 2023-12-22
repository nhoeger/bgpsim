import unittest
import sys
import os

import bgpsecsim.as_graph as as_graph
from bgpsecsim.asys import AS, AS_ID, Relation, Route, RoutingPolicy
from bgpsecsim.as_graph import ASGraph
from bgpsecsim.routing_policy import (
    DefaultPolicy, RPKIPolicy, PathEndValidationPolicy,
    BGPsecHighSecPolicy, BGPsecMedSecPolicy, BGPsecLowSecPolicy,
    RouteLeakPolicy, ASPAPolicy, ASCONESPolicy, DownOnlyPolicy
)
import bgpsecsim.experiments as experiments
import bgpsecsim.routing_policy as routing_policy

AS_REL_FILEPATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'as-rel-extended.txt')

#			  ------ 1 -----
#	         /       |      \
#           2  ----- 3       4
#          /  \    /   \   /   \
#         /    \  /     \ /     \
#        5 ----- 6 ----- 7 ----- 8
#       / \     / \     / \     / \
#      /   \   /   \   /   \   /   \
#     9    10 11   12 13   14 15   16
#    /                               \
#   /                                 \
#  17                                  18


class TestRouteLeakGraph(unittest.TestCase):
    def test_route_leak_provider_case(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        provider = graph.get_asys('2')
        local_as = graph.get_asys('6')
        local_as.policy = DownOnlyPolicy()

        path = [provider.as_id, local_as.as_id]

        new_route = Route(
            local_as.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False,
            local_data_part_do="",
        )

        # routing_policy.perform_down_only(new_route)
        assert not local_as.policy.forward_to(new_route,Relation.PROVIDER)
        assert local_as.policy.forward_to(new_route,Relation.CUSTOMER)
        assert not local_as.policy.forward_to(new_route,Relation.PEER)

    def test_route_customer_case(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        customer = graph.get_asys('11')
        local_as = graph.get_asys('6')
        local_as.policy = DownOnlyPolicy()

        path = [customer.as_id, local_as.as_id]

        new_route = Route(
            local_as.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False,
            local_data_part_do="",
        )

        assert local_as.policy.accept_route(new_route)
        assert local_as.policy.forward_to(new_route, Relation.CUSTOMER)
        assert len(new_route.local_data_part_do) != 0
        assert not local_as.policy.accept_route(new_route)

    def test_route_peer_case(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        customer = graph.get_asys('5')
        local_as = graph.get_asys('6')
        local_as.policy = DownOnlyPolicy()

        path = [customer.as_id, local_as.as_id]

        new_route = Route(
            local_as.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False,
            local_data_part_do="",
        )
        # TODO: Extend test case to check line 530 on routing_policy.py
        assert local_as.policy.accept_route(new_route)
        assert local_as.policy.forward_to(new_route, Relation.CUSTOMER)
        assert len(new_route.local_data_part_do) != 0
        assert not local_as.policy.accept_route(new_route)