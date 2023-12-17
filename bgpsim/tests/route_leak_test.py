import unittest
import sys
import os

import bgpsecsim.as_graph as as_graph
from bgpsecsim.asys import AS, AS_ID, Relation, Route, RoutingPolicy
from bgpsecsim.as_graph import ASGraph
from bgpsecsim.routing_policy import (
    DefaultPolicy, RPKIPolicy, PathEndValidationPolicy,
    BGPsecHighSecPolicy, BGPsecMedSecPolicy, BGPsecLowSecPolicy,
    RouteLeakPolicy, ASPAPolicy, ASCONESPolicy
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
    def route_leak_functionality(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        sent_from_provider = graph.get_asys('2')
        sent_from_customer = graph.get_asys('5')
        sent_from_client = graph.get_asys('11')
        local_as = graph.get_asys('6')
        send_to_provider = graph.get_asys('3')
        send_to_customer = graph.get_asys('7')
        send_to_client = graph.get_asys('12')

        assert True == True

    def test_route_leak_provider_case(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        provider = graph.get_asys('2')
        local_as = graph.get_asys('6')
        send_to_provider = graph.get_asys('3')
        send_to_customer = graph.get_asys('7')
        send_to_client = graph.get_asys('12')

        path = [provider.as_id, local_as.as_id]

        #tmp.append(provider.as_id)
        new_route = Route(
            local_as,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False,
            local_data_part_do=[1,2],
        )

        routing_policy.perform_down_only(new_route)
        print("Testing...")
        print("New Data part: " + new_route.local_data_part_do)
        print("Origin Invalid: " + new_route.origin_invalid)

        #print(len(route.local_data_part_do))

        assert True == True