import unittest
import sys
import os

import bgpsecsim.as_graph as as_graph
import bgpsecsim.experiments as experiments
from bgpsecsim.asys import AS, AS_ID, Relation, Route, RoutingPolicy
from bgpsecsim.as_graph import ASGraph
from bgpsecsim.routing_policy import (
    DefaultPolicy, RPKIPolicy, PathEndValidationPolicy,
    BGPsecHighSecPolicy, BGPsecMedSecPolicy, BGPsecLowSecPolicy,
    RouteLeakPolicy, ASPAPolicy, ASCONESPolicy, DownOnlyPolicy, OnlyToCustomerPolicy
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


class TestASGraph(unittest.TestCase):

    def test_new_approaches(self):
        new_file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'as_do_otc.txt')
        nx_graph = as_graph.parse_as_rel_file(new_file_path)
        graph = ASGraph(nx_graph)
        tier_one = graph.get_tierOne()
        tier_two = graph.get_tierTwo()
        tier_three = graph.get_tierThree()
        len_as = len(tier_one) + len(tier_two) + len(tier_three)
        default_counter = graph.get_number_of_policy_users("DefaultPolicy")
        print("Default counter: ", default_counter)
        run_test = True

        if run_test:
            # find promising tuples: attacker and victim with success rate > 0
            # Adds these candidates to promising_tuples
            current_best = 0
            promising_tuples = []
            new_candidates = []
            for i in range(1, len_as):
                for j in range(1, len_as):
                    victim = graph.get_asys(str(i))
                    attacker = graph.get_asys(str(j))
                    graph.clear_routing_tables()
                    graph.reset_policies()
                    attacker.policy = RouteLeakPolicy()
                    graph.find_routes_to(victim)
                    result = experiments.route_leak_success_rate(graph, attacker, victim)
                    if result > 0 and not promising_tuples.__contains__([victim, attacker]):
                        promising_tuples.append([victim, attacker])

            # Iterates through promising tuples to find combinations, where the success rate increases, even with
            # Down-Only deployment
            if len(promising_tuples) != 0:
                print("Iterating through candidates... ")
                for elem in promising_tuples:
                    victim = graph.get_asys(str(elem[0].as_id))
                    attacker = graph.get_asys(str(elem[1].as_id))
                    graph.clear_routing_tables()
                    graph.reset_policies()
                    attacker.policy = RouteLeakPolicy()
                    graph.find_routes_to(victim)
                    current_best_rate = experiments.route_leak_success_rate(graph, attacker, victim)
                    down_only_user = graph.get_number_of_policy_users("DownOnlyPolicy")
                    assert down_only_user == 0
                    tmp_counter = 0
                    for as_tier_one in tier_one:
                        graph.clear_routing_tables()
                        graph.get_asys(as_tier_one).policy = DownOnlyPolicy()
                        if graph.get_asys(as_tier_one) != attacker:
                            tmp_counter += 1
                        attacker.policy = RouteLeakPolicy()
                        graph.find_routes_to(victim)
                        down_only_user = graph.get_number_of_policy_users("DownOnlyPolicy")
                        assert down_only_user == tmp_counter
                        result = float(experiments.route_leak_success_rate(graph, attacker, victim))
                        if result > current_best_rate and not new_candidates.__contains__([victim, attacker]):
                            new_candidates.append([victim, attacker])
            else:
                print("No promising tuples. Abort!")

            # Iterate through these cases and print the Results
            if len(new_candidates) != 0:
                print("Found promising candidates!")
                for candidates in new_candidates:
                    # print("------------------------")
                    promising_array = []
                    victim = graph.get_asys(str(candidates[0].as_id))
                    attacker = graph.get_asys(str(candidates[1].as_id))
                    graph.clear_routing_tables()
                    graph.reset_policies()
                    attacker.policy = RouteLeakPolicy()
                    graph.find_routes_to(victim)
                    current_best_rate = float(experiments.route_leak_success_rate(graph, attacker, victim))
                    assert graph.get_number_of_policy_users("DownOnlyPolicy") == 0
                    # print("Attacker: ", str(candidates[1].as_id), "; Victim: ", str(candidates[0].as_id))
                    # print("Result: ", current_best_rate)
                    promising_array.append(current_best)
                    tmp_counter = 0
                    for as_tier_one in tier_one:
                        graph.clear_routing_tables()
                        graph.get_asys(as_tier_one).policy = DownOnlyPolicy()
                        attacker.policy = RouteLeakPolicy()
                        graph.find_routes_to(victim)
                        if graph.get_asys(as_tier_one) != attacker:
                            tmp_counter += 1
                        down_only_user = graph.get_number_of_policy_users("DownOnlyPolicy")
                        assert down_only_user == tmp_counter
                        result = float(experiments.route_leak_success_rate(graph, attacker, victim))
                        # print("Result: ", result)
                        promising_array.append(result)

                    if len(promising_array) >= 3:
                        if promising_array[1] < promising_array[2]:
                            print("#-----------------------------------#"
                                  "")
                            print("Attacker: ", str(candidates[1].as_id), "; Victim: ", str(candidates[0].as_id))
                            print("Array: ", promising_array)
        else:
            print("Not running test")

    def test_specific_pair(self):
        print("#---- Specific Test ----#.")
        new_file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'as_do_otc.txt')
        nx_graph = as_graph.parse_as_rel_file(new_file_path)
        graph = ASGraph(nx_graph)

        victim = graph.get_asys(str(14))
        attacker = graph.get_asys(str(15))
        graph.clear_routing_tables()
        graph.reset_policies()
        attacker.policy = RouteLeakPolicy()
        graph.find_routes_to(victim)
        result = float(experiments.route_leak_success_rate(graph, attacker, victim))
        print("Result: ", result)
        assert True

    '''   
    def test_parse_as_rel_file(self):
        graph = as_graph.parse_as_rel_file(AS_REL_FILEPATH)
        for i in range(1, 18):
            assert str(i) in graph.nodes
        assert graph.edges[('1', '4')]['customer'] == '4'
        assert graph.edges[('2', '6')]['customer'] == '6'
        assert graph.edges[('5', '6')]['customer'] is None

    def test_ASGraph_constructor(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        for i in range(1, 18):
            assert str(i) in graph.asyss
        assert graph.get_asys('1').get_relation(graph.get_asys('4')) == Relation.CUSTOMER
        assert graph.get_asys('4').get_relation(graph.get_asys('1')) == Relation.PROVIDER
        assert graph.get_asys('2').get_relation(graph.get_asys('6')) == Relation.CUSTOMER
        assert graph.get_asys('6').get_relation(graph.get_asys('2')) == Relation.PROVIDER
        assert graph.get_asys('5').get_relation(graph.get_asys('6')) == Relation.PEER
        assert graph.get_asys('6').get_relation(graph.get_asys('5')) == Relation.PEER

    def test_check_for_customer_provider_cycles(self):
        nx_graph = as_graph.parse_as_rel_file(AS_REL_FILEPATH)
        graph = ASGraph(nx_graph)
        self.assertFalse(graph.any_customer_provider_cycles())

        # Create a customer-provider cycle
        nx_graph.add_edge('1', '16', customer='1')
        graph = ASGraph(nx_graph)
        self.assertTrue(graph.any_customer_provider_cycles())

    def test_learn_routes(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        asys_8 = graph.get_asys('8')
        for asys in graph.asyss.values():
            graph.find_routes_to(asys_8)

        for asys in graph.asyss.values():
            assert '8' in asys.routing_table
            route = asys.routing_table['8']
            assert route.final == asys

    def test_ascones_object_creation(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        asys_8 = graph.get_asys('8')
        asys_7 = graph.get_asys('7')
        asys_8.create_new_ascones()
        asys_7.create_new_ascones()
        assert ('8', ['14', '15', '16']) == asys_8.get_ascones()
        assert asys_8.get_customers() == asys_8.get_ascones_customer()
        assert ('7', ['13', '14']) == asys_7.get_ascones()
        assert asys_7.get_customers() == asys_7.get_ascones_customer()

    def test_aspa_object_creation(self):
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))
        asys_8 = graph.get_asys('8')
        asys_7 = graph.get_asys('7')
        asys_8.create_new_aspa(graph)
        asys_7.create_new_aspa(graph)
        assert ('8', ['4']) == asys_8.get_aspa()
        assert asys_8.get_providers() == asys_8.get_aspa_providers()
        assert ('7', ['3', '4']) == asys_7.get_aspa()
        assert asys_7.get_providers() == asys_7.get_aspa_providers()

    def test_ascones_policy_assginment(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))
        for as_id in graph.get_tierOne() + graph.get_tierTwo():
            graph.get_asys(as_id).policy = ASCONESPolicy()
        assert graph.get_asys('8').policy.name == 'ASCONESPolicy'
        assert graph.get_asys('17').policy.name == 'DefaultPolicy'

    def test_aspa_policy_assginment(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))
        for as_id in graph.asyss.keys():
            graph.get_asys(as_id).policy = ASPAPolicy()
        assert graph.get_asys('8').policy.name == 'ASPAPolicy'

    ############################
    # ASPA UPSTREAM TEST CASES #
    ############################

    def test_aspa_case_01(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Only Customers, only a single hop
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('9')

        path = [victim.as_id, verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_02(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Only Customers
        # Slide15 Trajectory 1
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('1')

        path = [victim.as_id, '9', '5', '2', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_03(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - RouteLeak by AS6
        # Slide15 Trajectory 1
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('3')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]
        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_04(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - RouteLeak by AS6, but AS2 has no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('1')

        path = [victim.as_id, '9', '5', '2', '6', '3', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('2').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_05(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Only Customers, but AS9 has no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('1')

        path = [victim.as_id, '9', '5', '2', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('9').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_06(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Two customers, then lateral peer
        # Slide15 Trajectory 2
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('6')

        path = [victim.as_id, '9', '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_07(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Two customers, then lateral peer, but AS9 has no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('6')

        path = [victim.as_id, '9', '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('9').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_08(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Customer to Provider, to Peer, to Peer
        # Slide14 Trajectory 3
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('7')

        path = [victim.as_id, '5', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_09(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Customer to Provider, to Customer, to Peer
        # Slide14 Trajectory 2
        victim = graph.get_asys('5')
        verifying_as = graph.get_asys('7')

        path = [victim.as_id, '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_10(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Customer to Provider, to Peer, to Provider
        # Slide14 Trajectory 4
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('3')

        path = [victim.as_id, '5', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    ###############################
    ## ASPA DOWNSTREAM TEST CASES #
    ###############################

    def test_aspa_case_11(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Upstream sending route directly
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_12(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Customer of Upstream sending route
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('10')

        path = [victim.as_id, '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_13(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Peer of Upstream sending route
        victim = graph.get_asys('6')
        verifying_as = graph.get_asys('10')

        path = [victim.as_id, '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_14(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Upstream of Upstream sending route
        # Slide15 Trajectory 5
        victim = graph.get_asys('2')
        verifying_as = graph.get_asys('10')

        path = [victim.as_id, '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_15(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Peer of Upstream of Upstream sending route
        # Slide15 Trajectory 6
        victim = graph.get_asys('6')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_16(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape
        # Slide15 Trajectory 3
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('12')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_17(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape - Opposite direction
        victim = graph.get_asys('12')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '6', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_18(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex
        # Slide15 Trajectory 4
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_19(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex - Opposite direction
        victim = graph.get_asys('14')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '7', '3', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_20(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape, but AS5 has no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('12')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_21(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape - Opposite direction, but AS5 has no ASPA
        victim = graph.get_asys('12')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '6', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Valid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_22(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS5 has no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_23(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex - Opposite direction, but AS5 has no ASPA
        victim = graph.get_asys('14')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '7', '3', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_24(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape, but AS5 and AS6 have no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('12')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        graph.get_asys('6').aspa = None
        verifying_as.policy = ASPAPolicy()
        #print(routing_policy.perform_ASPA_algorithm(route))
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_25(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape - Opposite direction, but AS5 and AS6 have no ASPA
        victim = graph.get_asys('12')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '6', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        graph.get_asys('6').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_26(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS5 and AS6 have no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        graph.get_asys('6').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_27(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex - Opposite direction, but AS5 and AS6 have no ASPA
        victim = graph.get_asys('14')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '7', '3', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('5').aspa = None
        graph.get_asys('6').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_30(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 to Upstream
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '6', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_31(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 to Lateral peer
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '6', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_32(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 and again by AS7
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('18')

        path = [victim.as_id, '9', '5', '2', '6', '3', '7', '4', '8', '16', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)

    def test_aspa_case_33(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 and again by AS7, opposite direction
        victim = graph.get_asys('18')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '16', '8', '4', '7', '3', '6', '2', '5', '9', verifying_as.as_id]
        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        verifying_as.policy = ASPAPolicy()
        assert 'Invalid' == routing_policy.perform_ASPA_algorithm(route)



    ###############################
    # ASCONES UPSTREAM TEST CASES #
    ###############################

    def test_ascones_case_01(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Only Customers, only a single hop
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('9')

        path = [victim.as_id, verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_02(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Only Customers
        # Slide15 Trajectory 1
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('1')

        path = [victim.as_id, '9', '5', '2', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_03(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - RouteLeak by AS6
        # Slide15 Trajectory 1
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('3')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]
        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_04(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - RouteLeak by AS6, but AS6 has no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('1')

        path = [victim.as_id, '9', '5', '2', '6', '3', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('6').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_05(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Only Customers, but AS9 has no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('1')

        path = [victim.as_id, '9', '5', '2', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('9').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_06(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Two customers, then lateral peer
        # Slide15 Trajectory 2
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('6')

        path = [victim.as_id, '9', '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_07(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Two customers, then lateral peer, but AS9 has no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('6')

        path = [victim.as_id, '9', '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('9').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_08(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Customer to Provider, to Peer, to Peer
        # Slide14 Trajectory 3
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('7')

        path = [victim.as_id, '5', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_09(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Customer to Provider, to Customer, to Peer
        # Slide14 Trajectory 2
        victim = graph.get_asys('5')
        verifying_as = graph.get_asys('7')

        path = [victim.as_id, '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_10(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Upstream Path Verification - Customer to Provider, to Peer, to Provider
        # Slide14 Trajectory 4
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('3')

        path = [victim.as_id, '5', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    # ##################################
    # ## ASCONES DOWNSTREAM TEST CASES #
    # ##################################

    def test_ascones_case_11(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Upstream sending route directly
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_12(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Customer of Upstream sending route
        victim = graph.get_asys('9')
        verifying_as = graph.get_asys('10')

        path = [victim.as_id, '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_13(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Peer of Upstream sending route
        victim = graph.get_asys('6')
        verifying_as = graph.get_asys('10')

        path = [victim.as_id, '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_14(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Upstream of Upstream sending route
        # Slide15 Trajectory 5
        victim = graph.get_asys('2')
        verifying_as = graph.get_asys('10')

        path = [victim.as_id, '5', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_15(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Peer of Upstream of Upstream sending route
        # Slide15 Trajectory 6
        victim = graph.get_asys('6')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_16(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape
        # Slide15 Trajectory 3
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('12')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_17(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape - Opposite direction
        victim = graph.get_asys('12')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '6', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_18(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex
        # Slide15 Trajectory 4
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_19(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex - Opposite direction
        victim = graph.get_asys('14')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '7', '3', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Valid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_20(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape, but AS5 has no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('12')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_21(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape - Opposite direction, but AS5 has no ASCONES
        victim = graph.get_asys('12')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '6', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_22(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS5 has no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_23(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex - Opposite direction, but AS5 has no ASCONES
        victim = graph.get_asys('14')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '7', '3', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_24(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape, but AS5 and AS6 have no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('12')

        path = [victim.as_id, '9', '5', '2', '6', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        graph.get_asys('6').ascones = None
        verifying_as.policy = ASCONESPolicy()
        #print(routing_policy.perform_ASCONES_algorithm(route))
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_25(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape - Opposite direction, but AS5 and AS6 have no ASCONES
        victim = graph.get_asys('12')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '6', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        graph.get_asys('6').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_26(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS5 and AS6 have no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        graph.get_asys('6').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_27(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex - Opposite direction, but AS5 and AS6 have no ASCONES
        victim = graph.get_asys('14')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '7', '3', '2', '5', '9', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('5').ascones = None
        graph.get_asys('6').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_30(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 to Upstream
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '6', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_31(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 to Lateral peer
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '6', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_32(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 and again by AS7
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('18')

        path = [victim.as_id, '9', '5', '2', '6', '3', '7', '4', '8', '16', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_33(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        # Downstream Path Verification - Route Leak by AS6 and again by AS7, opposite direction
        victim = graph.get_asys('18')
        verifying_as = graph.get_asys('17')

        path = [victim.as_id, '16', '8', '4', '7', '3', '6', '2', '5', '9', verifying_as.as_id]
        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        verifying_as.policy = ASCONESPolicy()
        assert 'Invalid' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_34(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS2 at the top has no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('2').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)

    def test_ascones_case_35(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS2 and AS3 at the top have no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('2').ascones = None
        graph.get_asys('3').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)



    def test_aspa_case_36(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS2 and AS3 at the top have no ASPA
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASPA_objects_randomly(graph, 100)
        graph.get_asys('3').aspa = None
        graph.get_asys('5').aspa = None
        verifying_as.policy = ASPAPolicy()
        assert 'Unknown' == routing_policy.perform_ASPA_algorithm(route)

    def test_ascones_case_36(self):
        graph = ASGraph(as_graph.parse_as_rel_file_CAIDA(AS_REL_FILEPATH))

        #Downstream Path Verification - Inverted V Shape with p2p at apex, but AS2 and AS3 at the top have no ASCONES
        victim = graph.get_asys('17')
        verifying_as = graph.get_asys('14')

        path = [victim.as_id, '9', '5', '2', '3', '7', verifying_as.as_id]

        route = Route(
            victim.as_id,
            [graph.get_asys(x) for x in path],
            origin_invalid=False,
            path_end_invalid=False,
            authenticated=False
        )

        experiments.create_ASCONES_objects_randomly(graph, 100)
        graph.get_asys('2').ascones = None
        #graph.get_asys('3').ascones = None
        verifying_as.policy = ASCONESPolicy()
        assert 'Unknown' == routing_policy.perform_ASCONES_algorithm(route)
'''


if __name__ == '__main__':
    unittest.main()
