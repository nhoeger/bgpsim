import abc
from fractions import Fraction
import multiprocessing as mp
import multiprocessing.synchronize as mpsync
import networkx as nx
import random
import signal
import warnings
from typing import List, Tuple
import sys

from bgpsecsim.asys import Relation, AS, AS_ID
from bgpsecsim.as_graph import ASGraph
from bgpsecsim.routing_policy import (
    DefaultPolicy, RPKIPolicy, PathEndValidationPolicy,
    BGPsecHighSecPolicy, BGPsecMedSecPolicy, BGPsecLowSecPolicy,
    RouteLeakPolicy, ASPAPolicy, ASCONESPolicy, DownOnlyPolicy, OnlyToCustomerPolicy
)

PARALLELISM = 250


def figure2a_line_1_next_as(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.policy = PathEndValidationPolicy()
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_2_bgpsec_partial(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.policy = BGPsecMedSecPolicy()
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_3_two_hop(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=PathEndValidationPolicy())
    return figure2a_experiment(graph, trials, n_hops=2)


def figure2a_line_4_rpki(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_5_bgpsec_low_full(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=BGPsecLowSecPolicy())
    for asys in graph.asyss.values():
        asys.bgp_sec_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_5_bgpsec_med_full(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=BGPsecMedSecPolicy())
    for asys in graph.asyss.values():
        asys.bgp_sec_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_5_bgpsec_high_full(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=BGPsecHighSecPolicy())
    for asys in graph.asyss.values():
        asys.bgp_sec_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_6_aspa_partial(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=ASPAPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.aspa_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2aDownOnlyPartial(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    # TODO: Changed policies
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    i = 0
    for asys in graph.identify_top_isps(deployment):
        asys.rlm_enabled = True
        # TODO: Note: Added following line
        asys.policy = DownOnlyPolicy()
        i += 1
    print("ASes with enabled Down Only: ", i)
    # TODO: Note: Changed number of hops from 1 to 2
    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_7_aspa_optimal(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=ASPAPolicy())
    # Values here have to be set, to use ASPA for the desired percentage by AS categorized in certain Tier
    tierTwo = 50
    tierThree = 50

    for asys in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * tierTwo)):
        graph.get_asys(asys).aspa_enabled = True
    for asys in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * tierThree)):
        graph.get_asys(asys).aspa_enabled = True

    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line_7_down_only_optimal(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    # Values here have to be set, to use ASPA for the desired percentage by AS categorized in certain Tier
    tierTwo = 50
    tierThree = 50

    for asys in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * tierTwo)):
        graph.get_asys(asys).rlm_enabled = True
        graph.get_asys(asys).policy = DownOnlyPolicy

    for asys in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * tierThree)):
        graph.get_asys(asys).aspa_enabled = True
        graph.get_asys(asys).policy = DownOnlyPolicy

    return figure2a_experiment(graph, trials, n_hops=1)


def figure2a_line8_rlp(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    i = 0
    for asys in graph.asyss.values():
        i += 1
        asys.policy = DownOnlyPolicy()
        # asys.rlm_enabled = True
        # TODO: Changed hops from 2 to 1
    print("Enabled ASes: ", str(i))
    return figure2a_experiment(graph, trials, n_hops=2)


def figure2a_line_8_aspa_full(
        nx_graph: nx.Graph,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=ASPAPolicy())
    for asys in graph.asyss.values():
        asys.aspa_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


def run_trial(graph, victim_id, attacker_id, n_hops):
    victim = graph.get_asys(victim_id)
    if victim is None:
        raise ValueError(f"No AS with ID {victim_id}")
    attacker = graph.get_asys(attacker_id)
    if attacker is None:
        raise ValueError(f"No AS with ID {attacker_id}")

    graph.find_routes_to(victim)
    graph.hijack_n_hops(victim, attacker, n_hops)

    result = attacker_success_rate(graph, attacker, victim)

    # Avoid using unnecesary memory
    graph.clear_routing_tables()

    return result


def figure2a_experiment(
        graph: ASGraph,
        trials: List[Tuple[AS_ID, AS_ID]],
        n_hops: int
) -> List[Fraction]:
    trial_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    workers = [Figure2aExperiment(trial_queue, result_queue, graph, n_hops)
               for _ in range(PARALLELISM)]
    for worker in workers:
        worker.start()

    for trial in trials:
        trial_queue.put(trial)

    results = []
    for _ in range(len(trials)):
        result = result_queue.get()
        results.append(result)

    for worker in workers:
        worker.stop()
    for worker in workers:
        trial_queue.put(None)
    for worker in workers:
        worker.join()
    print("Results: ", result)

    return results


def figureRouteLeak_experiment_selective(
        graph: ASGraph,
        trials: List[Tuple[AS_ID, AS_ID]],
        deployment_ASPA_objects_list: List,
        deployment_ASPA_policy_list: List,
        algorithm: str
) -> List[Fraction]:
    trial_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    # Workers are being reused! Meaning that any change in the graph will affect later evaluations within the same worker!
    # Make sure to reset policies and routing tables when reusing a worker!
    workers = [FigureRouteLeakExperiment(trial_queue, result_queue, graph, deployment_ASPA_objects_list,
                                         deployment_ASPA_policy_list, algorithm)
               for _ in range(PARALLELISM)]
    for worker in workers:
        worker.start()

    for trial in trials:
        trial_queue.put(trial)

    results = []
    for _ in range(len(trials)):
        result = result_queue.get()
        results.append(result)

    for worker in workers:
        worker.stop()
    for worker in workers:
        trial_queue.put(None)
    for worker in workers:
        worker.join()

    return results


def figureRouteLeak_experiment_random(
        graph: ASGraph,
        trials: List[Tuple[AS_ID, AS_ID]],
        deployment: [int, int, int],
        aspa_deployment: [int, int, int, int, int, int],
        algorithm: str
) -> List[Fraction]:
    trial_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    # Workers are being reused! Meaning that any change in the graph will affect later evaluations within the same worker!
    # Make sure to reset policies and routing tables when reusing a worker!
    workers = [FigureRouteLeakExperimentRandom(trial_queue, result_queue, graph, [],
                                               [], algorithm, deployment, aspa_deployment)
               for _ in range(PARALLELISM)]
    for worker in workers:
        worker.start()

    for trial in trials:
        trial_queue.put(trial)

    results = []
    for _ in range(len(trials)):
        result = result_queue.get()
        results.append(result)

    for worker in workers:
        worker.stop()
    for worker in workers:
        trial_queue.put(None)
    for worker in workers:
        worker.join()

    return results


def figureRouteLeak_experiment_top_isps(
        graph: ASGraph,
        trials: List[Tuple[AS_ID, AS_ID]],
        deployment: List[int],
        algorithm: str
) -> List[Fraction]:
    trial_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    # Workers are being reused! Meaning that any change in the graph will affect later evaluations within the same worker!
    # Make sure to reset policies and routing tables when reusing a worker!
    workers = [FigureRouteLeakExperimentRandom(trial_queue, result_queue, graph, deployment, algorithm)
               for _ in range(PARALLELISM)]
    for worker in workers:
        worker.start()

    for trial in trials:
        trial_queue.put(trial)

    results = []
    for _ in range(len(trials)):
        result = result_queue.get()
        results.append(result)

    for worker in workers:
        worker.stop()
    for worker in workers:
        trial_queue.put(None)
    for worker in workers:
        worker.join()

    return results


def figureForgedOrigin_experiment_random(
        graph: ASGraph,
        trials: List[Tuple[AS_ID, AS_ID]],
        deployment_objects: int,
        deployment_policy: int,
        algorithm: str
) -> List[Fraction]:
    trial_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    # Workers are being reused! Meaning that any change in the graph will affect later evaluations within the same worker!
    # Make sure to reset policies and routing tables when reusing a worker!
    workers = [FigureForgedOriginPrefixHijackExperimentRandom(trial_queue, result_queue, graph, deployment_objects,
                                                              deployment_policy, algorithm)
               for _ in range(PARALLELISM)]
    for worker in workers:
        worker.start()

    for trial in trials:
        trial_queue.put(trial)

    results = []
    for _ in range(len(trials)):
        result = result_queue.get()
        results.append(result)

    for worker in workers:
        worker.stop()
    for worker in workers:
        trial_queue.put(None)
    for worker in workers:
        worker.join()

    return results


def figureForgedOrigin_experiment_selective(
        graph: ASGraph,
        trials: List[Tuple[AS_ID, AS_ID]],
        deployment_objects_list: List,
        deployment_policy_list: List,
        algorithm: str
) -> List[Fraction]:
    trial_queue: mp.Queue = mp.Queue()
    result_queue: mp.Queue = mp.Queue()
    # Workers are being reused! Meaning that any change in the graph will affect later evaluations within the same worker!
    # Make sure to reset policies and routing tables when reusing a worker!
    workers = [FigureForgedOriginPrefixHijackExperiment(trial_queue, result_queue, graph, deployment_objects_list,
                                                        deployment_policy_list, algorithm)
               for _ in range(PARALLELISM)]
    for worker in workers:
        worker.start()

    for trial in trials:
        trial_queue.put(trial)

    results = []
    for _ in range(len(trials)):
        result = result_queue.get()
        results.append(result)

    for worker in workers:
        worker.stop()
    for worker in workers:
        trial_queue.put(None)
    for worker in workers:
        worker.join()

    return results


def figure4_k_hop(nx_graph: nx.Graph, trials: List[Tuple[AS_ID, AS_ID]], n_hops: int) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    return figure2a_experiment(graph, trials, n_hops)


def figure7a(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.policy = PathEndValidationPolicy()
    return figure2a_experiment(graph, trials, n_hops=1)


def figure7b(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.policy = BGPsecMedSecPolicy()
    return figure2a_experiment(graph, trials, n_hops=1)


# ASPA deployed by Top 100 providers
def figure7c(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=ASPAPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.aspa_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


# ASPA deployed by 50% of all AS
def figure7d(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=ASPAPolicy())

    tierOne = 50
    tierTwo = 50
    tierThree = 50

    for asys in random.sample(graph.get_tierOne(), int(len(graph.get_tierOne()) / 100 * tierOne)):
        graph.get_asys(asys).aspa_enabled = True
    for asys in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * tierTwo)):
        graph.get_asys(asys).aspa_enabled = True
    for asys in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * tierThree)):
        graph.get_asys(asys).aspa_enabled = True
    return figure2a_experiment(graph, trials, n_hops=1)


def figure8_line_1_next_as(
        nx_graph: nx.Graph,
        deployment: int,
        p: float,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    results = []
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    for _ in range(20):
        for asys in graph.identify_top_isps(int(deployment / p)):
            if random.random() < p:
                asys.policy = PathEndValidationPolicy()
        results.extend(figure2a_experiment(graph, trials, n_hops=1))
    return results


def figure8_line_2_bgpsec_partial(
        nx_graph: nx.Graph,
        deployment: int,
        p: float,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    results = []
    graph = ASGraph(nx_graph, policy=RPKIPolicy())
    for _ in range(20):
        for asys in graph.identify_top_isps(int(deployment / p)):
            if random.random() < p:
                asys.policy = BGPsecMedSecPolicy()
        results.extend(figure2a_experiment(graph, trials, n_hops=1))
    return results


# Added for partial deployment evaluation
# TODO: Compare BGPsecMid with DownOnly Policy
def figure8_line_2_down_only(
        nx_graph: nx.Graph,
        deployment: int,
        p: float,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    results = []
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    for _ in range(20):
        for asys in graph.identify_top_isps(int(deployment / p)):
            if random.random() < p:
                asys.policy = DownOnlyPolicy()
        results.extend(figure2a_experiment(graph, trials, n_hops=1))
    return results


def figure8_line_3_aspa_partial(
        nx_graph: nx.Graph,
        deployment: int,
        p: float,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    results = []
    graph = ASGraph(nx_graph, policy=ASPAPolicy())
    for _ in range(20):
        for asys in graph.identify_top_isps(int(deployment / p)):
            if random.random() < p:
                asys.aspa_enabled = True
        results.extend(figure2a_experiment(graph, trials, n_hops=1))
    return results


def figure9_line_1_rpki_partial(
        nx_graph: nx.Graph,
        deployment: int,
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    for asys in graph.identify_top_isps(deployment):
        asys.policy = RPKIPolicy()
    return figure2a_experiment(graph, trials, n_hops=0)


def figure10_aspa(
        nx_graph: nx.Graph,
        # deployment over AS per percentage in [tier2, tier3]
        deployment: [int, int],
        trials: List[Tuple[AS_ID, AS_ID]],
        tierOne: int
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=ASPAPolicy())

    for asys in random.sample(graph.get_tierOne(), int(len(graph.get_tierOne()) / 100 * tierOne)):
        graph.get_asys(asys).aspa_enabled = True
    if deployment[0] != 0:
        for asys in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * deployment[0])):
            graph.get_asys(asys).aspa_enabled = True
    if deployment[1] != 0:
        for asys in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * deployment[1])):
            graph.get_asys(asys).aspa_enabled = True

    return figure2a_experiment(graph, trials, n_hops=1)


def figure10_down_only_random(
        nx_graph: nx.Graph,
        # deployment over AS per percentage in [tier2, tier3]
        deployment: [int, int],
        trials: List[Tuple[AS_ID, AS_ID]],
        tier_one: int,
        algorithm: str,
        aspa_deployment=None
) -> List[Fraction]:
    if aspa_deployment is None:
        # 0-2 = policy, 3-5 = object
        aspa_deployment = [0, 0, 0, 0, 0, 0]
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    return figureRouteLeak_experiment_random(graph, trials, [tier_one, deployment[1], deployment[0]],
                                             aspa_deployment, algorithm)


def figure10_down_only_top_isp(
        nx_graph: nx.Graph,
        # deployment over AS per percentage in [tier2, tier3]
        deployment: [int, int],
        trials: List[Tuple[AS_ID, AS_ID]],
        tier_one: int
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    return figureRouteLeak_experiment_top_isps(graph, trials, [tier_one, deployment[1], deployment[0]],
                                               "DownOnlyTopISP")


def figure10_down_only_combined(
        nx_graph: nx.Graph,
        # deployment over AS per percentage in [tier2, tier3]
        deployment: [int, int, int, int, int, int],
        trials: List[Tuple[AS_ID, AS_ID]]
) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    # TODO: Change called function
    return figureRouteLeak_experiment_top_isps(graph, trials, deployment, "Combined")


# In this method, each and every trial run chooses his ASPA ASes randomly for object creation and policy deployment (compared to choosing it once randomly for all trial runs)
def figure11_random_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                    trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    return figureRouteLeak_experiment_random(graph, trials, deployment_objects, deployment_policy, 'ASPA')


# In this method, ASPA ASes are selected by strategy and all trial runs deploy the same ASPA objects and ASes.
# Strategy: Objects and Policy are deployed by out-degree from top-to-bottom
def figure12_selective_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))

    # Select ASes for ASPA object deployment top-to-bottom by cust degree
    deployment_objects_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_objects))]

    # Select ASes for ASPA policy deployment top-to-bottom by cust degree
    deployment_policy_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_policy))]

    # print("ASes in total sorted: ", len(descending_by_cust_degree))
    # print("ASPA policy share: ", deployment_ASPA_policy)
    # print("ASPA object share: ", deployment_ASPA_objects)
    # print("ASes ASPA Objects selected: ", len(deployment_ASPA_objects_list))
    # print("ASes ASPA Policy selected: ", len(deployment_ASPA_policy_list))

    return figureRouteLeak_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list, 'ASPA')


# In this method, ASPA ASes are selected by strategy and all trial runs deploy the same ASPA objects and ASes.
# Strategy: Policies are deployed by out-degree from top-to-bottom, object creation from bottom-to-top
def figure14_selective_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))

    # Select ASes for ASPA object deployment bottom-to-top by cust degree
    if deployment_objects == 0:  # to avoid selection of whole array with [-0:]
        deployment_objects_list = []
    else:
        deployment_objects_list = descending_by_cust_degree[
                                  -(round(len(graph.asyss.keys()) / 100 * deployment_objects)):]

    # Select ASes for ASPA policy deployment top-to-bottom by cust degree
    deployment_policy_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_policy))]

    # print("ASes in total sorted: ", len(descending_by_cust_degree))
    # print("ASPA policy share: ", deployment_policy)
    # print("ASPA object share: ", deployment_objects)
    # print("ASes ASPA Objects selected: ", len(deployment_objects_list))
    # print("ASes ASPA Policy selected: ", len(deployment_policy_list))

    return figureRouteLeak_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list, 'ASPA')


# In this method, each and every trial run chooses his ASCONES ASes randomly for object creation and policy deployment (compared to choosing it once randomly for all trial runs)
def figure30_random_ascones_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    return figureRouteLeak_experiment_random(graph, trials, deployment_objects, deployment_policy, 'ASCONES')


# In this method, ASCONES ASes are selected by strategy and all trial runs deploy the same ASCONES objects and ASes.
# Strategy: Objects and Policy are deployed by out-degree from top-to-bottom
def figure31_selective_ascones_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                          trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))
    tierone_and_tiertwo_descending_by_cust_degree = graph.identify_top_isps_from_tierone_and_tiertwo(len(graph.asyss))

    # Select ASes for object deployment top-to-bottom by cust degree
    deployment_objects_list = tierone_and_tiertwo_descending_by_cust_degree[
                              :(round(len(tierone_and_tiertwo_descending_by_cust_degree) / 100 * deployment_objects))]

    # Select ASes for policy deployment top-to-bottom by cust degree
    deployment_policy_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_policy))]

    return figureRouteLeak_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list,
                                                'ASCONES')


# In this method, ASCONES ASes are selected by strategy and all trial runs deploy the same ASCONES objects and ASes.
# Strategy: Objects and Policy are deployed by out-degree. Objects from BottomToTop, Policy from TopToBottom
def figure32_selective_ascones_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                          trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))
    tierone_and_tiertwo_descending_by_cust_degree = graph.identify_top_isps_from_tierone_and_tiertwo(len(graph.asyss))

    # Select ASes for ASCONES object deployment bottom-to-top by cust degree from tier one and tier two ASes
    if deployment_objects == 0:  # to avoid selection of whole array with [-0:]
        deployment_objects_list = []
    else:
        deployment_objects_list = tierone_and_tiertwo_descending_by_cust_degree[-(
            round(len(tierone_and_tiertwo_descending_by_cust_degree) / 100 * deployment_objects)):]

    # Select ASes for ASCONES policy deployment top-to-bottom by cust degree from all ASes
    deployment_policy_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_policy))]

    return figureRouteLeak_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list,
                                                'ASCONES')


# In this method, each and every trial run chooses his ASPA ASes randomly for object creation and policy deployment (compared to choosing it once randomly for all trial runs)
# This method is for the forget-origin prefix hijack.
def figure40_random_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                    trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    return figureForgedOrigin_experiment_random(graph, trials, deployment_objects, deployment_policy, 'ASPA')


# In this method, ASPA ASes are selected by strategy and all trial runs deploy the same ASPA objects and ASes.
# Strategy: Objects and Policy are deployed by out-degree from top-to-bottom
# This method is for the forget-origin prefix hijack.
def figure42_selective_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))
    # print([asys.as_id for asys in descending_by_cust_degree])

    # Select ASes for ASPA object deployment top-to-bottom by cust degree
    deployment_objects_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_objects))]

    # Select ASes for ASPA policy deployment top-to-bottom by cust degree
    deployment_policy_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_policy))]

    # print("ASes in total sorted: ", len(descending_by_cust_degree))
    # print("ASPA policy share: ", deployment_policy)
    # print("ASPA object share: ", deployment_objects)
    # print("ASes ASPA Objects selected: ", len(deployment_objects_list))
    # print("ASes ASPA Policy selected: ", len(deployment_policy_list))

    return figureForgedOrigin_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list,
                                                   'ASPA')


# In this method, ASPA ASes are selected by strategy and all trial runs deploy the same ASPA objects and ASes.
# Strategy: Objects and Policy are deployed by out-degree. Objects from bottom-to-top and policy from top-to-bottom
# This method is for the forget-origin prefix hijack.
def figure43_selective_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))

    # Select ASes for ASPA object deployment bottom-to-top by cust degree
    if deployment_objects == 0:  # to avoid selection of whole array with [-0:]
        deployment_objects_list = []
    else:
        deployment_objects_list = descending_by_cust_degree[
                                  -(round(len(graph.asyss.keys()) / 100 * deployment_objects)):]

    # Select ASes for ASPA policy deployment top-to-bottom by cust degree
    deployment_policy_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_policy))]

    # print("ASes in total sorted: ", len(descending_by_cust_degree))
    # print("ASPA policy share: ", deployment_ASPA_policy)
    # print("ASPA object share: ", deployment_ASPA_objects)
    # print("ASes ASPA Objects selected: ", len(deployment_ASPA_objects_list))
    # print("ASes ASPA Policy selected: ", len(deployment_ASPA_policy_list))

    return figureForgedOrigin_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list,
                                                   'ASPA')


# In this method, ASPA ASes are selected by strategy and all trial runs deploy the same ASPA objects and ASes.
# Strategy: Objects are deployed by out-degree from top-to-bottom, Policies are deployed by out-degree from bottom-to-top
# This method is for the forget-origin prefix hijack.
def figure44_selective_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))
    # print([asys.as_id for asys in descending_by_cust_degree])

    # Select ASes for ASPA object deployment top-to-bottom by cust degree
    deployment_objects_list = descending_by_cust_degree[:(round(len(graph.asyss.keys()) / 100 * deployment_objects))]

    # Select ASes for ASPA object deployment bottom-to-top by cust degree
    if deployment_policy == 0:  # to avoid selection of whole array with [-0:]
        deployment_policy_list = []
    else:
        deployment_policy_list = descending_by_cust_degree[-(round(len(graph.asyss.keys()) / 100 * deployment_policy)):]

    return figureForgedOrigin_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list,
                                                   'ASPA')


# In this method, ASPA ASes are selected by strategy and all trial runs deploy the same ASPA objects and ASes.
# Strategy: Objects and Policies are deployed by out-degree from bottom-to-top
# This method is for the forget-origin prefix hijack.
def figure45_selective_aspa_deployment(nx_graph: nx.Graph, deployment_objects: int, deployment_policy: int,
                                       trials: List[Tuple[AS_ID, AS_ID]]) -> List[Fraction]:
    graph = ASGraph(nx_graph, policy=DefaultPolicy())
    descending_by_cust_degree = graph.identify_top_isps(len(graph.asyss))
    # print([asys.as_id for asys in descending_by_cust_degree])

    # Select ASes for ASPA object deployment bottom-to-top by cust degree
    if deployment_objects == 0:  # to avoid selection of whole array with [-0:]
        deployment_objects_list = []
    else:
        deployment_objects_list = descending_by_cust_degree[
                                  -(round(len(graph.asyss.keys()) / 100 * deployment_objects)):]

    # Select ASes for ASPA object deployment bottom-to-top by cust degree
    if deployment_policy == 0:  # to avoid selection of whole array with [-0:]
        deployment_policy_list = []
    else:
        deployment_policy_list = descending_by_cust_degree[-(round(len(graph.asyss.keys()) / 100 * deployment_policy)):]

    return figureForgedOrigin_experiment_selective(graph, trials, deployment_objects_list, deployment_policy_list,
                                                   'ASPA')


# Result is a fraction, shows the ratio of successful attacks to not attacked routes
def attacker_success_rate(graph: ASGraph, attacker: AS, victim: AS) -> Fraction:
    n_bad_routes = 0
    n_total_routes = 0
    for asys in graph.asyss.values():
        route = asys.get_route(victim.as_id)
        if route:
            n_total_routes += 1
            if attacker in route.path and route.path[route.path.index(
                    attacker) - 1] == victim:  # check that victim is one before avoid counting regular routes received by attacker
                n_bad_routes += 1
                # print('Attacker: ', str(attacker.as_id) + ' Victim: ' + str(victim.as_id) + ' Bad route: ', [asys.as_id for asys in route.path])
            # else:
            # print('Attacker: ', str(attacker.as_id) + ' Victim: ' + str(victim.as_id) + ' Regular route: ', [asys.as_id for asys in route.path])
    # Fraction gives the first value as numerator and the second as denominator
    # print('Bad routes: ' + str(n_bad_routes) + ' ; Total routes: ' + str(n_total_routes))
    return Fraction(n_bad_routes, n_total_routes) * 100


# Check if route contains a relationship that goes against the Gao-Rexford model
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


# This function returns a fraction of total vs. bad routes.
def route_leak_success_rate(graph: ASGraph, attacker: AS, victim: AS) -> Fraction:
    # print("Second attacker enum: ", attacker.as_id)
    n_bad_routes = 0
    n_total_routes = 0
    for asys in graph.asyss.values():
        route = asys.get_route(victim.as_id)
        if route:
            n_total_routes += 1
            offending_asys = leaked_route(route)
            if offending_asys:
                n_bad_routes += 1
                # print(offending_asys.as_id, ", ", attacker.as_id)
                # TODO: remove comment infront of if-statement
                if offending_asys.as_id != attacker.as_id:
                    raise Exception("Attacker mismatches offending AS")
                # print("Attacker mismatches offending AS")
    # print('Bad routes: ', n_bad_routes)
    # print('Total routes: ', n_total_routes)
    # print('----')
    # Fraction gives the first value as numerator and the second as denominator
    # print('Bad routes: ' + str(n_bad_routes) + ' ; Total routes: ' + str(n_total_routes))
    return Fraction(n_bad_routes, n_total_routes) * 100


class Experiment(mp.Process, abc.ABC):
    input_queue: mp.Queue
    output_queue: mp.Queue
    _stopped: mpsync.Event

    def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue):
        super().__init__(daemon=True)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._stopped = mp.Event()

    def stop(self):
        self._stopped.set()

    def run(self):
        signal.signal(signal.SIGINT, lambda _signo, _frame: self.stop())

        while not self._stopped.is_set():
            trial = self.input_queue.get()

            # A None input is just used to stop blocking on the queue, so we can check stopped.
            if trial is None:
                continue

            self.output_queue.put(self.run_trial(trial))

    # Creates an abstract class which has to be definded later on
    @abc.abstractmethod
    # raise is used to give own errors, in this case if anythin happens where now error was created for
    def run_trial(self, trial):
        raise NotImplementedError()


class Figure2aExperiment(Experiment):
    graph: ASGraph
    n_hops: int

    def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue, graph: ASGraph, n_hops: int):
        super().__init__(input_queue, output_queue)
        self.graph = graph
        self.n_hops = n_hops

    def run_trial(self, trial: Tuple[(AS_ID, AS_ID)]):
        graph = self.graph
        n_hops = self.n_hops
        # Takes the value passed by the function call by "trial" and assigns them to victim and attacker
        victim_id, attacker_id = trial
        tmp = graph.get_asys(victim_id).get_customers()
        tmp = graph.get_asys(victim_id).policy

        # Takes the desired AS as victim out of the full graph by its ID
        victim = graph.get_asys(victim_id)
        if victim is None:
            warnings.warn(f"No AS with ID {victim_id}")
            return Fraction(0, 1)

        # Takes AS of attacker out of graph, like did for the victim
        attacker = graph.get_asys(attacker_id)
        if attacker is None:
            warnings.warn(f"No AS with ID {attacker_id}")
            return Fraction(0, 1)

        # starts to find a new routing table and executes the attack onto it by n hops
        graph.clear_routing_tables()
        graph.find_routes_to(victim)
        graph.hijack_n_hops(victim, attacker, n_hops)
        # graph.ro

        result = attacker_success_rate(graph, attacker, victim)

        return result


def show_policies(graph):
    default_policy = 0
    route_leak_policy = 0
    aspa_policy = 0
    down_only_policy = 0
    show_policies_by_tier(graph)
    for asys in graph.asyss:
        if graph.get_asys(asys).policy.name == 'DefaultPolicy':
            default_policy += 1
        elif graph.get_asys(asys).policy.name == 'RouteLeakPolicy':
            route_leak_policy += 1
        elif graph.get_asys(asys).policy.name == 'ASPAPolicy':
            aspa_policy += 1
        elif graph.get_asys(asys).policy.name == 'DownOnlyPolicy':
            down_only_policy += 1
        else:
            raise Exception('ERROR: Unknown policy in play!')
    print('Policies counter: \n Default: ' + str(default_policy) + '\n RouteLeak: ' + str(route_leak_policy) +
          '\n ASPA: ' + str(aspa_policy) + '\n DO: ' + str(down_only_policy))


def show_policies_by_tier(graph):
    for i in range(1, 4):
        show_policies_by_specified_tier(graph, i)


def show_policies_by_specified_tier(graph, tier):
    tmp_str = ""
    list = []
    if tier == 1:
        list = graph.get_tierOne()
        tmp_str = "One"
    elif tier == 2:
        list = graph.get_tierTwo()
        tmp_str = "Two"
    elif tier == 3:
        list = graph.get_tierThree()
        tmp_str = "Three"
    default_policy = 0
    route_leak_policy = 0
    aspa_policy = 0
    down_only_policy = 0
    otc_policy = 0
    for asys in list:
        compare_to = graph.get_asys(asys).policy.name
        if compare_to == 'DefaultPolicy':
            default_policy += 1
        elif compare_to == 'RouteLeakPolicy':
            route_leak_policy += 1
        elif compare_to == 'ASPAPolicy':
            aspa_policy += 1
        elif compare_to == 'DownOnlyPolicy':
            down_only_policy += 1
        elif compare_to == 'OnlyToCustomerPolicy':
            otc_policy += 1
        else:
            raise Exception('ERROR: Unknown policy in play!')

    print("Tier", tmp_str, ": Default: " + str(default_policy) + "; RouteLeak: " + str(route_leak_policy) +
          "; ASPA: " + str(aspa_policy) + "; DO: " + str(down_only_policy) + "; OTC: " + str(otc_policy))


def show_aspa_objects(graph):
    for asys in graph.asyss:
        aspa_object = graph.get_asys(asys).get_aspa()
        print(aspa_object)


def show_aspa_objects_count(graph):
    n = 0
    for asys in graph.asyss:
        aspa_object = graph.get_asys(asys).get_aspa()
        if aspa_object != None:
            n += 1
    print('Total of ASPA objects', n)


# create ASCONES objects for only tier one and two ASes according to deployment fraction
def create_ASCONES_objects_randomly(graph, deployment_ASCONES_objects):
    random.seed(None)
    sample = graph.get_tierOne() + graph.get_tierTwo()
    for as_id in random.sample(sample, round(len(sample) / 100 * deployment_ASCONES_objects)):
        graph.get_asys(as_id).create_new_ascones()
        # graph.get_asys(as_id).create_dummy_aspa()


def do_otc_randomly(graph, deployment: [int, int, int], algorithm: str, aspa_input=None):
    if len(deployment) != 3:
        warnings.warn("Parsed deployment does not match required format.")
    policy = DownOnlyPolicy()
    if algorithm == "DownOnly":
        policy = DownOnlyPolicy()
    elif algorithm == "OTC":
        policy = OnlyToCustomerPolicy()
    elif algorithm == "ASPA":
        if aspa_input is None:
            raise Exception("No ASPA deployment parsed for ASPA deployment!")
        aspa_deployment_random(graph, aspa_input)
        return
    elif algorithm == "Combined":
        if aspa_input is None:
            raise Exception("No ASPA deployment parsed for combined deployment!")
        aspa_deployment_random(graph, aspa_input)
    else:
        warnings.warn("No valid algorithm parsed.")
    tier_one = deployment[0]
    tier_two = deployment[1]
    tier_three = deployment[2]

    if tier_one != 0:
        for as_id in random.sample(graph.get_tierOne(), int(len(graph.get_tierOne()) / 100 * tier_one)):
            graph.get_asys(as_id).policy = policy
    if tier_two != 0:
        for as_id in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * tier_two)):
            graph.get_asys(as_id).policy = policy
    if tier_three != 0:
        for as_id in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * tier_three)):
            graph.get_asys(as_id).policy = policy


def down_only_top_isp(graph, deployment: [int, int, int], algorithm: str, aspa_input=None):
    if len(deployment) != 3:
        warnings.warn("Parsed deployment does not match required format.")
    policy = DownOnlyPolicy()
    if algorithm == "DownOnly":
        policy = DownOnlyPolicy()
    elif algorithm == "OTC":
        policy = OnlyToCustomerPolicy()
    elif algorithm == "ASPA":
        if aspa_input is None:
            raise Exception("No ASPA deployment parsed for ASPA deployment!")
        aspa_deployment_top_isp(graph, aspa_input)
        return
    elif algorithm == "Combined":
        if aspa_input is None:
            raise Exception("No ASPA deployment parsed for combined deployment!")
        aspa_deployment_top_isp(graph, aspa_input)
    else:
        warnings.warn("No valid algorithm parsed.")
    tier_one = deployment[0]
    tier_two = deployment[1]
    tier_one_top_isp = graph.identify_top_isp_from_tier_one(int(len(graph.get_tierOne()) / 100 * tier_one))
    tier_two_top_isp = graph.identify_top_isp_from_tier_two(int(len(graph.get_tierTwo()) / 100 * tier_two))

    if tier_one != 0:
        for as_object in tier_one_top_isp:
            as_number = as_object.as_id
            graph.get_asys(as_number).policy = policy
    if tier_two != 0:
        for as_object in tier_two_top_isp:
            as_number = as_object.as_id
            graph.get_asys(as_number).policy = policy


def aspa_deployment_top_isp(graph: ASGraph, deployment: [int, int, int, int, int, int]):
    if len(deployment) != 6:
        raise Exception("Parsed deployment does not match requirements!")
    policy = ASPAPolicy()
    tier_one_policy = deployment[0]
    tier_two_policy = deployment[1]
    tier_three_policy = deployment[2]
    tier_one_object = deployment[3]
    tier_two_object = deployment[4]
    tier_three_object = deployment[5]
    tier_one_top_isp_policy = graph.identify_top_isp_from_tier_one(int(len(graph.get_tierOne()) / 100 * tier_one_policy))
    tier_two_top_isp_policy = graph.identify_top_isp_from_tier_two(int(len(graph.get_tierTwo()) / 100 * tier_two_policy))
    tier_one_top_isp_object = graph.identify_top_isp_from_tier_one(int(len(graph.get_tierOne()) / 100 * tier_one_object))
    tier_two_top_isp_object = graph.identify_top_isp_from_tier_two(int(len(graph.get_tierTwo()) / 100 * tier_two_object))

    if tier_one_policy != 0:
        for as_id in tier_one_top_isp_policy:
            as_number = as_id.as_id
            graph.get_asys(as_number).policy = policy
    if tier_two_policy != 0:
        for as_id in tier_two_top_isp_policy:
            as_number = as_id.as_id
            graph.get_asys(as_number).policy = policy
    if tier_three_policy != 0:
        limit = int(len(graph.get_tierThree()) / 100 * tier_three_policy)
        for i in range(0, limit):
            as_id = graph.get_tierThree()[i]
            graph.get_asys(as_id).policy = policy
    if tier_one_object != 0:
        for as_id in tier_one_top_isp_object:
            as_number = as_id.as_id
            graph.get_asys(as_number).create_new_aspa(graph)
    if tier_two_object != 0:
        for as_id in tier_two_top_isp_object:
            as_number = as_id.as_id
            graph.get_asys(as_number).create_new_aspa(graph)
    if tier_three_object != 0:
        limit = int(len(graph.get_tierThree()) / 100 * tier_three_object)
        for i in range(0, limit):
            as_id = graph.get_tierThree()[i]
            graph.get_asys(as_id).create_new_aspa(graph)

def aspa_deployment_random(graph: ASGraph, deployment: [int, int, int, int, int, int]):
    if len(deployment) != 6:
        raise Exception("Parsed deployment does not match requirements!")
    policy = ASPAPolicy()
    tier_one_policy = deployment[0]
    tier_two_policy = deployment[1]
    tier_three_policy = deployment[2]
    tier_one_object = deployment[3]
    tier_two_object = deployment[4]
    tier_three_object = deployment[5]

    if tier_one_policy != 0:
        for as_id in random.sample(graph.get_tierOne(), int(len(graph.get_tierOne()) / 100 * tier_one_policy)):
            graph.get_asys(as_id).policy = policy
    if tier_two_policy != 0:
        for as_id in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * tier_two_policy)):
            graph.get_asys(as_id).policy = policy
    if tier_three_policy != 0:
        for as_id in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * tier_three_policy)):
            graph.get_asys(as_id).policy = policy
    if tier_one_object != 0:
        for as_id in random.sample(graph.get_tierOne(), int(len(graph.get_tierOne()) / 100 * tier_one_object)):
            graph.get_asys(as_id).create_new_aspa(graph)
    if tier_two_object != 0:
        for as_id in random.sample(graph.get_tierTwo(), int(len(graph.get_tierTwo()) / 100 * tier_two_object)):
            graph.get_asys(as_id).create_new_aspa(graph)
    if tier_three_object != 0:
        for as_id in random.sample(graph.get_tierThree(), int(len(graph.get_tierThree()) / 100 * tier_three_object)):
            graph.get_asys(as_id).create_new_aspa(graph)


# create ASPA objects for all ASes according to deployment fraction
def create_ASPA_objects_randomly(graph, deployment_ASPA_objects):
    random.seed(None)
    for as_id in random.sample(graph.asyss.keys(), round(len(graph.asyss.keys()) / 100 * deployment_ASPA_objects)):
        graph.get_asys(as_id).create_new_aspa(graph)
        # graph.get_asys(as_id).create_dummy_aspa()


# create ASCONES objects for all ASes according to list parameter
def create_ASCONES_objects(graph, deployment_ASCONES_objects):
    for asys in deployment_ASCONES_objects:
        asys.create_new_ascones()
        # graph.get_asys(as_id).create_dummy_aspa()


# create ASPA objects for all ASes according to list parameter
def create_ASPA_objects(graph, deployment_ASPA_objects):
    for asys in deployment_ASPA_objects:
        asys.create_new_aspa(graph)
        # graph.get_asys(as_id).create_dummy_aspa()


# create ASCONES policies for all ASes according to deployment fraction
def create_ASCONES_policies_randomly(graph, deployment_ASCONES_policy):
    random.seed(None)
    for as_id in random.sample(graph.asyss.keys(), round(len(graph.asyss.keys()) / 100 * deployment_ASCONES_policy)):
        graph.get_asys(as_id).policy = ASCONESPolicy()


# create ASPA policies for all ASes according to deployment fraction
def create_ASPA_policies_randomly(graph, deployment_ASPA_policy):
    random.seed(None)
    for as_id in random.sample(graph.asyss.keys(), round(len(graph.asyss.keys()) / 100 * deployment_ASPA_policy)):
        graph.get_asys(as_id).policy = ASPAPolicy()


# create ASCONES policies for all ASes according to list parameter
def create_ASCONES_policies(graph, deployment_ASCONES_policy):
    for asys in deployment_ASCONES_policy:
        asys.policy = ASCONESPolicy()


# create ASPA policies for all ASes according to list parameter
def create_ASPA_policies(graph, deployment_ASPA_policy):
    for asys in deployment_ASPA_policy:
        asys.policy = ASPAPolicy()


class FigureRouteLeakExperimentRandom(Experiment):
    graph: ASGraph
    deployment: List[int]

    # def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue, graph: ASGraph, deployment: List[int],
    #             algorithm: str, ):
    def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue, graph: ASGraph, deployment_objects_list: List,
                 deployment_policy_list: List, algorithm: str, deployment=None, aspa_deployment=None):
        super().__init__(input_queue, output_queue)
        self.graph = graph
        self.deployment_objects_list = deployment_objects_list
        self.deployment_policy_list = deployment_policy_list
        self.deployment = deployment
        self.aspa_deployment = aspa_deployment
        self.algorithm = algorithm

    def run_trial(self, trial: Tuple[(AS_ID, AS_ID)]):
        graph = self.graph
        algorithm = self.algorithm

        # Takes the value passed by the function call by "trial" and assigns them to victim and attacker
        victim_id, attacker_id = trial
        graph.reset_policies()
        graph.clear_rpki_objects()

        # Takes the desired AS as victim out of the full graph by its ID
        victim = graph.get_asys(victim_id)
        if victim is None:
            warnings.warn(f"No AS with ID {victim_id}")
            return Fraction(0, 1)

        # Takes AS of attacker out of graph, like did for the victim
        attacker = graph.get_asys(attacker_id)
        if attacker is None:
            warnings.warn(f"No AS with ID {attacker_id}")
            return Fraction(0, 1)

        if algorithm == 'DownOnly':
            if self.deployment is None:
                warnings.warn(f"No deployment parsed!")
                return Fraction(0, 1)
            do_otc_randomly(graph, self.deployment, algorithm)

        elif algorithm == 'OTC':
            if self.deployment is None:
                warnings.warn(f"No deployment parsed!")
                return Fraction(0, 1)
            do_otc_randomly(graph, self.deployment, algorithm)

        elif algorithm == 'DownOnlyTopISP':
            if self.deployment is None:
                warnings.warn(f"No deployment parsed!")
                return Fraction(0, 1)
            down_only_top_isp(graph, self.deployment, 'DownOnly', self.aspa_deployment)

        elif algorithm == 'OTC_ISP':
            if self.deployment is None:
                warnings.warn(f"No deployment parsed!")
                return Fraction(0, 1)
            down_only_top_isp(graph, self.deployment, 'OTC', self.aspa_deployment)

        elif algorithm == 'Combined':
            do_otc_randomly(graph, self.deployment, algorithm, self.aspa_deployment)
        elif algorithm == 'Combined_ISP':
            down_only_top_isp(graph, self.deployment, 'Combined', self.aspa_deployment)
        elif algorithm == 'ASPA':
            do_otc_randomly(graph, self.aspa_deployment, algorithm)
        elif algorithm == 'ASPA_ISP':
            down_only_top_isp(graph, self.deployment, 'ASPA', self.aspa_deployment)

        attacker.policy = RouteLeakPolicy()  # This will change the attackers policy to leak all routes

        # starts to find a new routing table and executes the attack onto it by n hops
        graph.clear_routing_tables()
        graph.find_routes_to(victim)
        result = route_leak_success_rate(graph, attacker, victim)

        return result


class FigureRouteLeakExperiment(Experiment):
    graph: ASGraph
    deployment: int

    def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue, graph: ASGraph, deployment_objects_list: List,
                 deployment_policy_list: List, algorithm: str):
        super().__init__(input_queue, output_queue)
        self.graph = graph
        self.deployment_objects_list = deployment_objects_list
        self.deployment_policy_list = deployment_policy_list
        self.algorithm = algorithm

    def run_trial(self, trial: Tuple[(AS_ID, AS_ID)]):
        graph = self.graph
        deployment_objects_list = self.deployment_objects_list
        deployment_policy_list = self.deployment_policy_list
        algorithm = self.algorithm
        # Takes the value passed by the function call by "trial" and assigns them to victim and attacker
        victim_id, attacker_id = trial

        graph.reset_policies()  # Reset all AS policies to DefaultPolicy
        graph.clear_rpki_objects()  # Reset all AS policies to DefaultPolicy

        # Takes the desired AS as victim out of the full graph by its ID
        victim = graph.get_asys(victim_id)
        if victim is None:
            warnings.warn(f"No AS with ID {victim_id}")
            return Fraction(0, 1)

        # Takes AS of attacker out of graph, like did for the victim
        attacker = graph.get_asys(attacker_id)
        if attacker is None:
            warnings.warn(f"No AS with ID {attacker_id}")
            return Fraction(0, 1)

        if algorithm == 'ASPA':
            # Set ASPA policies for ASes in the current graph
            create_ASPA_policies(graph, deployment_policy_list)
            # Creates ASPA objects for ASes in the current graph
            create_ASPA_objects(graph, deployment_objects_list)
        elif algorithm == 'ASCONES':
            # Set ASPA policies for ASes in the current graph
            create_ASCONES_policies(graph, deployment_policy_list)
            # Creates ASPA objects for ASes in the current graph
            create_ASCONES_objects(graph, deployment_objects_list)

        attacker.policy = RouteLeakPolicy()  # This will change the attackers policy to leak all routes
        # print("Route Leak AS: ", attacker.as_id)
        # print("Victim AS: ", victim.as_id)

        # show_policies(graph)  # Checking for the distribution of policies
        # show_aspa_objects(graph) # Show all ASPA objects of graph
        # show_aspa_objects_count(graph) # Show count of all ASPA objects of graph

        # starts to find a new routing table and executes the attack onto it by n hops
        graph.clear_routing_tables()
        graph.find_routes_to(victim)
        #        graph.hijack_n_hops(victim, attacker, n_hops)

        result = route_leak_success_rate(graph, attacker, victim)

        return result


class FigureForgedOriginPrefixHijackExperimentRandom(Experiment):
    graph: ASGraph
    deployment: int

    def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue, graph: ASGraph, deployment_objects: int,
                 deployment_policy: int, algorithm: str):
        super().__init__(input_queue, output_queue)
        self.graph = graph
        self.deployment_objects = deployment_objects
        self.deployment_policy = deployment_policy
        self.algorithm = algorithm

    def run_trial(self, trial: Tuple[(AS_ID, AS_ID)]):
        graph = self.graph
        deployment_objects = self.deployment_objects
        deployment_policy = self.deployment_policy
        algorithm = self.algorithm
        # Takes the value passed by the function call by "trial" and assigns them to victim and attacker
        victim_id, attacker_id = trial

        graph.reset_policies()  # Reset all AS policies to DefaultPolicy
        graph.clear_rpki_objects()  # Reset all AS policies to DefaultPolicy

        # Takes the desired AS as victim out of the full graph by its ID
        victim = graph.get_asys(victim_id)
        if victim is None:
            warnings.warn(f"No AS with ID {victim_id}")
            return Fraction(0, 1)

        # Takes AS of attacker out of graph, like did for the victim
        attacker = graph.get_asys(attacker_id)
        if attacker is None:
            warnings.warn(f"No AS with ID {attacker_id}")
            return Fraction(0, 1)

        if algorithm == 'ASPA':
            # Set ASPA policies for ASes in the current graph
            create_ASPA_policies_randomly(graph, deployment_policy)
            create_ASPA_objects_randomly(graph, deployment_objects)
        elif algorithm == 'ASCONES':
            create_ASCONES_policies_randomly(graph, deployment_policy)
            create_ASCONES_objects_randomly(graph, deployment_objects)

        attacker.policy = DefaultPolicy()  # This will change the attackers policy to default policy in order not to drop her own hijacked route

        # starts to find a new routing table and executes the attack onto it by n hops
        graph.clear_routing_tables()
        graph.find_routes_to(victim)
        graph.hijack_n_hops(victim, attacker, 1)

        result = attacker_success_rate(graph, attacker, victim)

        return result


class FigureForgedOriginPrefixHijackExperiment(Experiment):
    graph: ASGraph
    deployment: int

    def __init__(self, input_queue: mp.Queue, output_queue: mp.Queue, graph: ASGraph, deployment_objects_list: List,
                 deployment_policy_list: List, algorithm: str):
        super().__init__(input_queue, output_queue)
        self.graph = graph
        self.deployment_objects_list = deployment_objects_list
        self.deployment_policy_list = deployment_policy_list
        self.algorithm = algorithm

    def run_trial(self, trial: Tuple[(AS_ID, AS_ID)]):
        graph = self.graph
        deployment_objects_list = self.deployment_objects_list
        deployment_policy_list = self.deployment_policy_list
        algorithm = self.algorithm
        # Takes the value passed by the function call by "trial" and assigns them to victim and attacker
        victim_id, attacker_id = trial

        graph.reset_policies()  # Reset all AS policies to DefaultPolicy
        graph.clear_rpki_objects()  # Reset all AS policies to DefaultPolicy

        # Takes the desired AS as victim out of the full graph by its ID
        victim = graph.get_asys(victim_id)
        if victim is None:
            warnings.warn(f"No AS with ID {victim_id}")
            return Fraction(0, 1)

        # Takes AS of attacker out of graph, like did for the victim
        attacker = graph.get_asys(attacker_id)
        if attacker is None:
            warnings.warn(f"No AS with ID {attacker_id}")
            return Fraction(0, 1)

        if algorithm == 'ASPA':
            # Set ASPA policies for ASes in the current graph
            create_ASPA_policies(graph, deployment_policy_list)
            # Creates ASPA objects for ASes in the current graph
            create_ASPA_objects(graph, deployment_objects_list)
        elif algorithm == 'ASCONES':
            # Set ASPA policies for ASes in the current graph
            create_ASCONES_policies(graph, deployment_policy_list)
            # Creates ASPA objects for ASes in the current graph
            create_ASCONES_objects(graph, deployment_objects_list)

        attacker.policy = DefaultPolicy()  # This will change the attackers policy to default policy in order not to drop her own hijacked route
        # print("Route Leak AS: ", attacker.as_id)
        # print("Victim AS: ", victim.as_id)

        # show_policies(graph)  # Checking for the distribution of policies
        # show_aspa_objects(graph) # Show all ASPA objects of graph
        # show_aspa_objects_count(graph) # Show count of all ASPA objects of graph

        # starts to find a new routing table and executes the attack onto it by n hops
        graph.clear_routing_tables()
        graph.find_routes_to(victim)
        graph.hijack_n_hops(victim, attacker, 1)

        result = attacker_success_rate(graph, attacker, victim)

        return result
