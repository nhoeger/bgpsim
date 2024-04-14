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
Route_Pair = tuple[Route, str]

def check_trial(*args) -> bool:
    for elem_args in args:
        last_elem = elem_args[0]
        for elem in elem_args:
            if elem > last_elem:
                return True
            last_elem = elem
    return False


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


def tmp_success(graph: ASGraph, attacker: AS, victim: AS):
    return_routes = []
    for asys in graph.asyss.values():
        route = asys.get_route(victim.as_id)
        if route:
            offending_asys = leaked_route(route)
            if offending_asys:
                pair1: Route_Pair = (route, route.local_data_part_do)
                return_routes.append(pair1)
    return return_routes


def compare_all_routes(first_route: [Route], second_route: [Route]):
    unique_to_first = [route for route in first_route if route not in second_route]
    unique_to_second = [route for route in second_route if route not in first_route]

    differing_routes = unique_to_first + unique_to_second
    return differing_routes


def find_increase(attacker_as: str, victim_as: str, graph: ASGraph):
    victim = graph.get_asys(victim_as)
    attacker = graph.get_asys(attacker_as)
    graph.clear_routing_tables()
    graph.reset_policies()
    attacker.policy = RouteLeakPolicy()
    graph.find_routes_to(victim)
    initial_result = experiments.new_success_rate(graph, attacker, victim)

    tier_one = graph.get_tierOne()
    tier_two = graph.get_tierTwo()
    tier_three = graph.get_tierThree()
    len_as = tier_one + tier_two + tier_three
    result_array = [initial_result]
    switched_ases = ['0']
    printer = False
    for ases in len_as:
        graph.clear_routing_tables()
        switched_ases.append(ases)
        graph.get_asys(ases).policy = DownOnlyPolicy()
        graph.find_routes_to(victim)
        result = float(experiments.new_success_rate(graph, attacker, victim))
        result_array.append(result)
        if result > initial_result:
            printer = True
    # A: 18, V: 5; Increase detected
    if printer:
        print("+---------------------------------+")
        #experiments.show_policies(graph)
        print("Result: ", result_array)
        print("Attacker: ", attacker_as, "; Victim: ", victim_as)
        print("ASes:   ", switched_ases)
        print("+---------------------------------+")


def detailed_test(attacker_as: str, victim_as: str, graph: ASGraph):
    victim = graph.get_asys(victim_as)
    attacker = graph.get_asys(attacker_as)
    graph.clear_routing_tables()
    graph.reset_policies()
    attacker.policy = RouteLeakPolicy()
    graph.find_routes_to(victim)
    initial_result = experiments.new_success_rate(graph, attacker, victim)
    print("Initial Result: ", initial_result)
    print("#------------------------------------------------------#")
    graph.clear_routing_tables()
    graph.reset_policies()
    graph.get_asys('1').policy = DownOnlyPolicy()
    attacker.policy = RouteLeakPolicy()
    graph.find_routes_to(victim)
    initial_result = experiments.new_success_rate(graph, attacker, victim)
    print("Second Result: ", initial_result)
    print("#------------------------------------------------------#")
    graph.clear_routing_tables()
    graph.reset_policies()
    graph.get_asys('2').policy = DownOnlyPolicy()
    attacker.policy = RouteLeakPolicy()
    graph.find_routes_to(victim)
    initial_result = experiments.new_success_rate(graph, attacker, victim)
    print("Third Result: ", initial_result)

class TestASGraph(unittest.TestCase):

    def test_new_approaches(self):
        #nx_graph = as_graph.parse_as_rel_file('/home/nils/Routing/bgpsim/bgpsim/caida-data/20221101.as-rel.txt')
        nx_graph = as_graph.parse_as_rel_file(AS_REL_FILEPATH)
        graph = ASGraph(nx_graph)
        # print("Loaded graph")
        tier_one = graph.get_tierOne()
        tier_two = graph.get_tierTwo()
        tier_three = graph.get_tierThree()
        tier_one_top_isp = graph.identify_top_isp_from_tier_one(int(len(graph.get_tierOne()) / 100 * 25))
        len_as = len(tier_one) + len(tier_two) + len(tier_three)
        run_test = False
        new_collection = False
        down_only_as = []

        if run_test:
            victim = graph.get_asys('211076')
            attacker = graph.get_asys('4775')
            graph.clear_routing_tables()
            graph.reset_policies()
            attacker.policy = RouteLeakPolicy()
            graph.find_routes_to(victim)
            initial_result = experiments.new_success_rate(graph, attacker, victim)
            print("Initial result: ", initial_result)
            routes_saved = tmp_success(graph, attacker, victim)
            graph.clear_routing_tables()
            graph.get_asys('174').policy = OnlyToCustomerPolicy()
            experiments.show_policies(graph)
            graph.find_routes_to(victim)
            other_routes = tmp_success(graph, attacker, victim)
            result = float(experiments.new_success_rate(graph, attacker, victim))
            print("Second result: ", result)
            compare_all_routes(other_routes, routes_saved)

        if new_collection:
            current_trial_results = []
            current_switched_as = []
            total_iterations = len_as * len_as
            progress = 0
            tier_one_progress = 0
            for i in range(1, len_as):
                for j in range(1, len_as):
                    as_ids: List[AS_ID] = list(nx_graph.nodes)
                    [asn1, asn2] = random.sample(as_ids, 2)

                    force_as = True
                    if force_as:
                        asn1 = '211076'
                        asn2 = '4775'
                        # First DO AS is: 174

                    progress += 1
                    percent_complete = (progress / total_iterations) * 100
                    print(f"Overall Progress: {percent_complete:.2f}%")
                    print(f"Pair: Victim:", asn1, ", Attacker:", asn2, "; Total Iterations: ", progress, "/", total_iterations)
                    victim = graph.get_asys(asn1)
                    attacker = graph.get_asys(asn2)
                    graph.clear_routing_tables()
                    graph.reset_policies()
                    attacker.policy = RouteLeakPolicy()
                    graph.find_routes_to(victim)
                    old_result = experiments.new_success_rate(graph, attacker, victim)
                    print("Old result: ", old_result)
                    current_trial_results.append(old_result)
                    routes_saved = tmp_success(graph, attacker, victim)
                    for as_tier_one in tier_one_top_isp:
                        as_number = as_tier_one.as_id
                        down_only_as.append(as_number)
                        tier_one_progress += 1
                        percent_complete_tier = (tier_one_progress / len(tier_one_top_isp)) * 100
                        sys.stdout.write('\r' + f"Tier 1 Progress: {percent_complete_tier:.2f}%")
                        sys.stdout.flush()
                        graph.clear_routing_tables()
                        graph.get_asys(as_number).policy = DownOnlyPolicy()
                        current_switched_as.append(as_number)
                        graph.find_routes_to(victim)
                        other_routes = tmp_success(graph, attacker, victim)
                        result = float(experiments.new_success_rate(graph, attacker, victim))
                        print('\n' + "Result: ", result, "; Down Only ASes: ", down_only_as)
                        if result > old_result:
                            print("First Route: ", other_routes[0])
                            print("Relationship: ", graph.get_asys('1').get_relation(graph.get_asys('174')))
                            print("Relationship 1 to 11537: ", graph.get_asys('1').get_relation(graph.get_asys('11537')))
                            compare_all_routes(other_routes, routes_saved)
                            break
                        else:
                            other_routes = routes_saved
                        current_trial_results.append(result)
                        old_result = result
                    print(current_trial_results)
                    if check_trial(current_trial_results):
                        break
                    current_trial_results = []

            else:
                print("No promising tuples. Abort!")


    def test_find_pair(self):
        nx_graph = as_graph.parse_as_rel_file(AS_REL_FILEPATH)
        graph = ASGraph(nx_graph)
        tier_one = graph.get_tierOne()
        tier_two = graph.get_tierTwo()
        tier_three = graph.get_tierThree()
        len_as = tier_one + tier_two + tier_three

        # Good Pairs
        # (6/ 17)
        # find_increase('6', '17', graph)
        detailed_test('6', '17', graph)
        #for attacker_as in len_as:
        #     for victim_as in len_as:
        #         find_increase(attacker_as, victim_as, graph)

    #def test_specific_pair(self):
    #    print("#---- Specific Test ----#.")
    #    current_switched_as = []
    #    new_file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'as_do_otc.txt')
    #    nx_graph = as_graph.parse_as_rel_file(new_file_path)
    #    graph = ASGraph(nx_graph)#######
#
 #       victim = graph.get_asys(str(14))
  #      attacker = graph.get_asys(str(15))
   #     graph.clear_routing_tables()
    #    graph.reset_policies()
     #   attacker.policy = RouteLeakPolicy()
     #   graph.find_routes_to(victim)
     #   result = float(experiments.route_leak_success_rate(graph, attacker, victim))
     #   print("Result: ", result)#
#
 #       tier_one = graph.get_tierOne()
  #      print("Tier one: ", tier_one)
   #     for as_tier_one in tier_one:
    #        graph.clear_routing_tables()
     #       graph.get_asys(as_tier_one).policy = DownOnlyPolicy()
      #      current_switched_as.append(as_tier_one)
       #     graph.find_routes_to(victim)
       #     result = float(experiments.route_leak_success_rate(graph, attacker, victim))
       #     print("Down Only ASes: ", current_switched_as)
       #     print(Fore.RED + "Result: ", result, Fore.WHITE)

        #assert True


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
