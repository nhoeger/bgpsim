import sys
from fractions import Fraction
import itertools
import math
import time
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy
import numpy as np
import random
import statistics
from typing import List, Sequence, Tuple
from matplotlib import cm
from numpy import asarray
from numpy import savetxt
import pickle as pkl
from timeit import default_timer as timer
from datetime import timedelta

from bgpsecsim.asys import AS_ID
import bgpsecsim.as_graph as as_graph
from bgpsecsim.as_graph import ASGraph
import bgpsecsim.experiments as experiments
import other.evaluation as eval


def get_attacks():
    return [
        ("Syria Telecom attacks Youtube-1", "attacks/STE-1.txt", "caida-data/20141201.as-rel.txt"),
        ("Syria Telecom attacks Youtube-2", "attacks/STE-2.txt", "caida-data/20141201.as-rel.txt"),
        ("Indosat attacks various ASes", "attacks/Indosat.txt", "caida-data/20110101.as-rel.txt"),
        # Turk Telecom was in 3/2014, but 12/2013 is as close as CAIDA has, for some reason
        ("Turk Telecom attacks DNS servers", "attacks/Turk Telecom.txt", "caida-data/20131201.as-rel.txt"),
        ("Opin Kerfi attacks CenturyTel", "attacks/Opin Kerfi.txt", "caida-data/20130701.as-rel.txt")
    ]


def get_content_providers() -> List[AS_ID]:
    # This list was from 2013. Major content providers have likely changed.
    # TODO: Get updated list.
    return [
        15169,  # Google
        22822,  # Limelight
        20940,  # Akamai
        8075,  # Microsoft
        10310,  # Yahoo
        16265,  # Leaseweb
        15133,  # Edgecast
        16509,  # Amazon
        32934,  # Facebook
        2906,  # Netflix
        4837,  # QQ
        13414,  # Twitter
        40428,  # Pandora
        14907,  # Wikipedia
        714,  # Apple
        23286,  # Hulu
        38365,  # Baidu
    ]


def get_current_content_providers() -> List[AS_ID]:
    return [
        20940,  # Akamai
        16509,  # Amazon
        714,  # Apple
        32934,  # Facebook
        15169,  # Google
        8075,  # Microsoft
        2906  # Netflix
    ]


def target_content_provider_trials(nx_graph: nx.Graph, n_trials: int, providers: List[AS_ID]) -> List[
    Tuple[AS_ID, AS_ID]]:
    content_providers_set = set(providers)
    asyss_set = set(nx_graph.nodes)
    assert content_providers_set <= asyss_set

    as_ids: List[AS_ID] = list(asyss_set - content_providers_set)
    attackers = random.choices(as_ids, k=math.ceil(n_trials / len(providers)))
    return list(itertools.product(providers, attackers))


def uniform_random_trials(nx_graph: nx.Graph, n_trials: int) -> List[Tuple[AS_ID, AS_ID]]:
    as_ids: List[AS_ID] = list(nx_graph.nodes)
    return [random_pair(as_ids) for _ in range(n_trials)]


def trials_with_predefined_attackers(nx_graph: nx.Graph, n_trials: int, attacker: List[AS_ID]) -> List[
    Tuple[AS_ID, AS_ID]]:
    as_ids: List[AS_ID] = list(nx_graph.nodes)
    pairs = [random_pair(as_ids) for _ in range(n_trials)]
    new_pairs = []
    index = 0
    for pair in pairs:
        new_pairs.append((list(pair)[:-1] + [attacker[index]]))
        index = index + 1
    return new_pairs


def get_route_leak_trial(graph: ASGraph) -> Tuple[AS_ID, AS_ID]:
    asyss_with_providers = graph.tierTwo + graph.tierThree
    victim = random.sample(asyss_with_providers, 1)
    victim_providers = graph.get_providers(victim)
    attacker = random.sample(victim_providers, 1)
    return (victim, attacker)


# might be obsolete
def route_leak_trials(nx_graph: nx.Graph, n_trials: int) -> List[Tuple[AS_ID, AS_ID]]:
    graph = ASGraph(nx_graph)  # Create ASGraph to check for neighbor relationships
    return [get_route_leak_trial(graph) for _ in range(n_trials)]


# This function returns a list without any repetition
def find_asyss_without_repetition(nx_graph: nx.Graph, tier: int, n: int) -> List[AS_ID]:
    graph = ASGraph(nx_graph)  # Create ASGraph to check for neighbor relationships
    if tier == 1:
        return random.sample(graph.tierOne, n)
    elif tier == 2:
        return random.sample(graph.tierTwo, n)
    elif tier == 3:
        return random.sample(graph.tierThree, n)
    return False


# This function returns a list with a possibly repeated list of entries
def find_asyss_with_repetition(nx_graph: nx.Graph, tier: int, n: int) -> List[AS_ID]:
    graph = ASGraph(nx_graph)  # Create ASGraph to check for neighbor relationships
    if tier == 1:
        return [random.choice(graph.tierOne) for _ in range(n)]
    elif tier == 2:
        return [random.choice(graph.tierTwo) for _ in range(n)]
    elif tier == 3:
        return [random.choice(graph.tierThree) for _ in range(n)]
    return False


def figure2a(filename: str, nx_graph: nx.Graph, n_trials: int):
    trials = uniform_random_trials(nx_graph, n_trials)
    return figure2(filename, nx_graph, trials)


def figure2b(filename: str, nx_graph: nx.Graph, n_trials: int):
    """
    This one is a little weird. The paper says "We evaluated, for each victim content provider, the
    success rate of an attacker drawn uniformly at random." But the graph has only one line, so we
    assume the success rate is averaged over them.
    """
    trials = target_content_provider_trials(nx_graph, n_trials, get_content_providers())
    return figure2(filename, nx_graph, trials)


def figure2(filename: str, nx_graph: nx.Graph, trials: List[Tuple[AS_ID, AS_ID]]):
    # Here the percentage of deployment is set, current from 0 to full deployment by top ISP, incrementing by 10% everytime
    deployments = np.arange(0, 110, 10)

    line1_results = []
    for deployment in deployments:
        print(f"Path-End (deployment = {deployment})")
        line1_results.append(fmean(experiments.figure2a_line_1_next_as(nx_graph, deployment, trials)))
    print("Path-End: ", line1_results)

    # line2_results = []
    # for deployment in deployments:
    #    print(f"BGPsec in partial deployment (deployment = {deployment})")
    #    line2_results.append(fmean(experiments.figure2a_line_2_bgpsec_partial(nx_graph, deployment, trials)))
    # print("BGPsec in partial deployment: ", line2_results)

    # line3_results = fmean(experiments.figure2a_line_3_two_hop(nx_graph, trials))
    # print("2-hop: ", line3_results)

    line4_results = fmean(experiments.figure2a_line_4_rpki(nx_graph, trials))
    print("RPKI (full deployment): ", line4_results)

    line5_results = fmean(experiments.figure2a_line_5_bgpsec_med_full(nx_graph, trials))
    print("BGPsec (full deployment, legacy allowed): ", line5_results)

    line6_results = []
    for deployment in deployments:
        print(f"ASPA in partial deployment (deployment = {deployment})")
        line6_results.append(fmean(experiments.figure2a_line_6_aspa_partial(nx_graph, deployment, trials)))
    print("ASPA in partial deployment: ", line6_results)

    line7_results = fmean(experiments.figure2a_line_7_aspa_optimal(nx_graph, trials))
    print("ASPA (50% deployment) ", line7_results)

    plt.figure(figsize=(10, 7))
    plt.plot(deployments, line1_results, label="Path-end-validation (partial deployment)")
    # plt.plot(deployments, line2_results, label="BGPsec (partial deployment)")
    # plt.plot(deployments, np.repeat(line3_results, 11), label="2-hop")
    plt.plot(deployments, np.repeat(line4_results, 11), label="RPKI (full deployment)", linestyle="--")
    plt.plot(deployments, np.repeat(line5_results, 11), label="BGPsec (full deployment, legacy allowed)",
             linestyle="--")
    plt.plot(deployments, line6_results, label="ASPA (partial deployment)")
    plt.plot(deployments, np.repeat(line7_results, 11), label="ASPA (50% deployment)", linestyle="--")
    plt.legend()
    plt.xlabel("Deployment at number of top ISPs, ranked by customer count")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.show()
    # plt.savefig(filename)


def figure2a1(filename: str, nx_graph: nx.Graph, trials: List[Tuple[AS_ID, AS_ID]]):
    # Here the percentage of deployment is set, current from 0 to full deployment by top ISP,
    # incrementing by 10% everytime
    print("Running Figure 2a1")
    deployments = np.arange(0, 110, 10)
    full_mode = False
    aspa_enable = False

    # down_only_results = []
    # for deployment in deployments:
    #    print(f"Down Only (deployment = {deployment})")
    #    tmp = fmean(experiments.figure2aDownOnlyPartial(nx_graph, deployment, trials))
    #    print("Appending: ", tmp)
    #    down_only_results.append(tmp)

    # print("Down Only in partial Deployment: ", down_only_results)

    # line8_results = fmean(experiments.figure2a_line8_rlp(nx_graph, trials))
    # print("Down Only in partial deployment: ", line8_results)
    p = 0.75
    down_only_results = []
    rand_state = random.getstate()
    for deployment in deployments:
        print(f"ASPA in partial deployment (deployment = {deployment})")
        random.setstate(rand_state)
        down_only_results.append(fmean(experiments.figure8_line_2_down_only(nx_graph, deployment, p, trials)))
    print("Down Only in partial deployment: ", down_only_results)

    if aspa_enable:
        line6_results = []
        for deployment in deployments:
            print(f"ASPA in partial deployment (deployment = {deployment})")
            line6_results.append(fmean(experiments.figure2a_line_6_aspa_partial(nx_graph, deployment, trials)))
        print("ASPA in partial deployment: ", line6_results)

        line7_results = fmean(experiments.figure2a_line_7_aspa_optimal(nx_graph, trials))
        print("ASPA (50% deployment) ", line7_results)

    if full_mode:
        line1_results = []
        for deployment in deployments:
            print(f"Path-End (deployment = {deployment})")
            line1_results.append(fmean(experiments.figure2a_line_1_next_as(nx_graph, deployment, trials)))
        print("Path-End: ", line1_results)

        line2_results = []
        for deployment in deployments:
            print(f"BGPsec in partial deployment (deployment = {deployment})")
            line2_results.append(fmean(experiments.figure2a_line_2_bgpsec_partial(nx_graph, deployment, trials)))
        print("BGPsec in partial deployment: ", line2_results)

        line3_results = fmean(experiments.figure2a_line_3_two_hop(nx_graph, trials))
        print("2-hop: ", line3_results)

        line4_results = fmean(experiments.figure2a_line_4_rpki(nx_graph, trials))
        print("RPKI (full deployment): ", line4_results)

        line5_results = fmean(experiments.figure2a_line_5_bgpsec_med_full(nx_graph, trials))
        print("BGPsec (full deployment, legacy allowed): ", line5_results)

    plt.figure(figsize=(10, 7))
    plt.plot(deployments, down_only_results, label="Down Only Partial Deployment")
    # plt.plot(deployments, np.repeat(line8_results, 11), label="DownOnly", linestyle="--")
    if full_mode:
        plt.plot(deployments, line1_results, label="Path-end-validation (partial deployment)")
        plt.plot(deployments, line2_results, label="BGPsec (partial deployment)")
        plt.plot(deployments, np.repeat(line3_results, 11), label="2-hop")
        plt.plot(deployments, np.repeat(line4_results, 11), label="RPKI (full deployment)", linestyle="--")
        plt.plot(deployments, np.repeat(line5_results, 11), label="BGPsec (full deployment, legacy allowed)",
                 linestyle="--")
    if aspa_enable:
        plt.plot(deployments, np.repeat(line6_results, 11), label="ASPA partial deployment", linestyle="--")
        plt.plot(deployments, np.repeat(line7_results, 11), label="ASPA (50% deployment)", linestyle="--")
        # plt.plot(deployments, np.repeat(line8_results, 11), label="ASPA", linestyle="--")
    plt.legend()
    plt.xlabel("Deployment at number of top ISPs, ranked by customer count")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.show()


def figure3a(filename: str, nx_graph: nx.Graph, n_trials: int):
    large_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 250, None))
    stub_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 0, 0))
    trials = [(random.choice(stub_asyss), random.choice(large_asyss)) for _ in range(n_trials)]
    return figure2(filename, nx_graph, trials)


def figure3b(filename: str, nx_graph: nx.Graph, n_trials: int):
    large_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 250, None))
    stub_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 0, 0))
    trials = [(random.choice(large_asyss), random.choice(stub_asyss)) for _ in range(n_trials)]
    return figure2(filename, nx_graph, trials)


def figure3c(filename: str, nx_graph: nx.Graph, n_trials: int):
    large_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 250, None))
    stub_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 0, 0))
    trials = [(random.choice(stub_asyss), random.choice(large_asyss)) for _ in range(n_trials)]
    # TODO: Note: Changed figure from figure2a to figure2a1
    return figure2a1(filename, nx_graph, trials)


def figure4(filename: str, nx_graph: nx.Graph, n_trials: int):
    trials = uniform_random_trials(nx_graph, n_trials)

    hops = np.arange(0, 11)

    line1_results = []
    for n_hops in hops:
        print(f"k-hop attacker (k={n_hops})")
        line1_results.append(fmean(experiments.figure4_k_hop(nx_graph, trials, n_hops)))
    print("k-hop attacker: ", line1_results)

    line2_results = fmean(experiments.figure2a_line_5_bgpsec_med_full(nx_graph, trials))
    print("BGPsec (full deployment, legacy allowed): ", line2_results)

    line3_results = fmean(experiments.figure2a_line_8_aspa_full(nx_graph, trials))
    print("ASPA (full deployment) ", line3_results)

    line4_results = fmean(experiments.figure2a_line_7_aspa_optimal(nx_graph, trials))
    print("ASPA (50% deployment) ", line4_results)

    plt.figure(figsize=(10, 5))
    plt.plot(hops, line1_results, label="k-hop attacker")
    plt.plot(hops, np.repeat(line2_results, 11), label="BGPsec (full deployment, legacy allowed)", linestyle="--")
    plt.plot(hops, np.repeat(line4_results, 11), label="ASPA (50% deployment)", linestyle="--")
    plt.plot(hops, np.repeat(line3_results, 11), label="ASPA (full deployment)", linestyle="--")
    plt.legend()
    plt.xlabel("Hops")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure7a(filename: str, nx_graph: nx.Graph, n_trials: int):
    results = []
    attacks = get_attacks()

    for (label, filepath, as_rel_file) in attacks:
        nx_graph = as_graph.parse_as_rel_file(as_rel_file)
        print("Loaded graph for ", label)

        with open(filepath) as f:
            attackers = None
            targets = []
            # Expects 1 attacker, n victims, comments beginning with #
            for l in f:
                if l[0] == '#':
                    continue
                if attackers == None:
                    attackers = [int(l)]
                    continue
                targets.append(int(l))

        trials = list(itertools.product(targets, attackers))

        deployments = np.arange(0, 110, 10)

        attack_results = []
        for deployment in deployments:
            attack_results.append(fmean(experiments.figure7a(nx_graph, deployment, trials)))
        results.append(attack_results)
        print(label, attack_results)

    plt.figure(figsize=(10, 5))
    for i in range(len(results)):
        plt.plot(deployments, results[i], label=attacks[i][0])
    plt.legend()
    plt.xlabel("Deployment (top ISPs)")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure7b(filename: str, nx_graph: nx.Graph, n_trials: int):
    results = []
    attacks = get_attacks()

    for (label, filepath, as_rel_file) in attacks:
        nx_graph = as_graph.parse_as_rel_file(as_rel_file)
        print("Loaded graph for ", label)

        with open(filepath) as f:
            attackers = None
            targets = []
            # Expects 1 attacker, n victims, comments beginning with #
            for l in f:
                if l[0] == '#':
                    continue
                if attackers == None:
                    attackers = [int(l)]
                    continue
                targets.append(int(l))

        trials = list(itertools.product(targets, attackers))

        deployments = np.arange(0, 110, 10)

        attack_results = []
        for deployment in deployments:
            attack_results.append(fmean(experiments.figure7b(nx_graph, deployment, trials)))
        results.append(attack_results)
        print(label, attack_results)

    plt.figure(figsize=(10, 5))
    for i in range(len(results)):
        plt.plot(deployments, results[i], label=attacks[i][0])
    plt.legend()
    plt.xlabel("Deployment (top ISPs)")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure7c(filename: str, nx_graph: nx.Graph, n_trials: int):
    results = []
    attacks = get_attacks()

    for (label, filepath, as_rel_file) in attacks:
        nx_graph = as_graph.parse_as_rel_file(as_rel_file)
        print("Loaded graph for ", label)

        with open(filepath) as f:
            attackers = None
            targets = []
            # Expects 1 attacker, n victims, comments beginning with #
            for l in f:
                if l[0] == '#':
                    continue
                if attackers == None:
                    attackers = [int(l)]
                    continue
                targets.append(int(l))

        trials = list(itertools.product(targets, attackers))

        deployments = np.arange(0, 110, 10)

        attack_results = []
        for deployment in deployments:
            attack_results.append(fmean(experiments.figure7c(nx_graph, deployment, trials)))
        results.append(attack_results)
        print(label, attack_results)

    plt.figure(figsize=(10, 5))
    for i in range(len(results)):
        plt.plot(deployments, results[i], label=attacks[i][0])
    plt.legend()
    plt.xlabel("Deployment (top ISPs)")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure7d(filename: str, nx_graph: nx.Graph, n_trials: int):
    results = []
    attacks = get_attacks()

    for (label, filepath, as_rel_file) in attacks:
        nx_graph = as_graph.parse_as_rel_file(as_rel_file)
        print("Loaded graph for ", label)

        with open(filepath) as f:
            attackers = None
            targets = []
            # Expects 1 attacker, n victims, comments beginning with #
            for l in f:
                if l[0] == '#':
                    continue
                if attackers == None:
                    attackers = [int(l)]
                    continue
                targets.append(int(l))

        trials = list(itertools.product(targets, attackers))

        deployments = np.arange(0, 110, 10)

        attack_results = []
        for deployment in deployments:
            attack_results.append(fmean(experiments.figure7d(nx_graph, deployment, trials)))
        results.append(attack_results)
        print(label, attack_results)

    plt.figure(figsize=(10, 5))
    for i in range(len(results)):
        plt.plot(deployments, results[i], label=attacks[i][0])
    plt.legend()
    plt.xlabel("Deployment (top ISPs)")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


# TODO: All results the same -> Rework
def figure8(filename: str, nx_graph: nx.Graph, n_trials: int, p: float):
    larfigure8age_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 250, None))
    stub_asyss = list(as_graph.asyss_by_customer_count(nx_graph, 0, 0))
    trials = [(random.choice(large_asyss), random.choice(stub_asyss)) for _ in range(n_trials)]

    deployments = np.arange(0, 110, 10)

    rand_state = random.getstate()

    # line1_results = []
    # for deployment in deployments:
    #    print(f"Next-AS (deployment = {deployment})")
    #    random.setstate(rand_state)
    #    line1_results.append(fmean(experiments.figure8_line_1_next_as(nx_graph, deployment, p, trials)))
    # print("Next-AS: ", line1_results)

    # line2_results = []
    # for deployment in deployments:
    #    print(f"BGPsec in partial deployment (deployment = {deployment})")
    #    random.setstate(rand_state)
    #    line2_results.append(fmean(experiments.figure8_line_2_bgpsec_partial(nx_graph, deployment, p, trials)))
    # print("BGPsec in partial deployment: ", line2_results)
    line_down_only_results = []
    for deployment in deployments:
        print(f"Down Only in partial deployment (deployment = {deployment})")
        random.setstate(rand_state)
        line_down_only_results.append(fmean(experiments.figure8_line_2_bgpsec_partial(nx_graph, deployment, p, trials)))
    print("Down Only in partial deployment: ", line_down_only_results)

    # line3_results = fmean(experiments.figure2a_line_3_two_hop(nx_graph, trials))
    # print("2-hop: ", line3_results)

    # line4_results = fmean(experiments.figure2a_line_4_rpki(nx_graph, trials))
    # print("RPKI (full deployment): ", line4_results)

    # line5_results = fmean(experiments.figure2a_line_5_bgpsec_med_full(nx_graph, trials))
    # print("BGPsec (full deployment, legacy allowed): ", line5_results)

    line6_results = []
    for deployment in deployments:
        print(f"ASPA in partial deployment (deployment = {deployment})")
        random.setstate(rand_state)
        line6_results.append(fmean(experiments.figure8_line_3_aspa_partial(nx_graph, deployment, p, trials)))
    print("ASPA in partial deployment: ", line6_results)

    # line7_results = fmean(experiments.figure2a_line_7_aspa_optimal(nx_graph, trials))
    # print("ASPA (50% deployment): ", line7_results)

    plt.figure(figsize=(10, 7))
    # plt.plot(deployments, line1_results, label="path-end-validation")
    plt.plot(deployments, line_down_only_results, label="Down Only in partial deployment")
    # plt.plot(deployments, np.repeat(line3_results, 11), label="2-hop")
    # plt.plot(deployments, np.repeat(line4_results, 11), label="RPKI (full deployment)", linestyle="--")
    # plt.plot(deployments, np.repeat(line5_results, 11), label="BGPsec (full deployment, legacy allowed)", linestyle="--")
    plt.plot(deployments, line6_results, label="ASPA in partial deployment")
    # plt.plot(deployments, np.repeat(line7_results, 11), label="ASPA (50% deployment)", linestyle="--")
    plt.legend()
    plt.xlabel("Expected Deployment (top ISPs)")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure8a(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure8(filename, nx_graph, n_trials, p=0.75)


def figure8b(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure8(filename, nx_graph, n_trials, p=0.50)


def figure8c(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure8(filename, nx_graph, n_trials, p=0.25)


def figure9a(filename: str, nx_graph: nx.Graph, n_trials: int):
    trials = uniform_random_trials(nx_graph, n_trials)
    return figure9(filename, nx_graph, trials)


def figure9b(filename: str, nx_graph: nx.Graph, n_trials: int):
    trials = target_content_provider_trials(nx_graph, n_trials, get_content_providers())
    return figure9(filename, nx_graph, trials)


def figure9b_update(filename: str, nx_graph: nx.Graph, n_trials: int):
    trials = target_content_provider_trials(nx_graph, n_trials, get_current_content_providers())
    return figure9(filename, nx_graph, trials)


def figure9(filename: str, nx_graph: nx.Graph, trials: List[Tuple[AS_ID, AS_ID]]):
    deployments = np.arange(0, 110, 10)

    line1_results = []
    for deployment in deployments:
        print(f"Prefix hijack (deployment = {deployment})")
        line1_results.append(fmean(experiments.figure9_line_1_rpki_partial(nx_graph, deployment, trials)))
    print("Prefix hijack: ", line1_results)

    line2_results = fmean(experiments.figure2a_line_4_rpki(nx_graph, trials))
    print("RPKI (full deployment): ", line2_results)

    plt.figure(figsize=(10, 5))
    plt.plot(deployments, line1_results, label="Prefix hijack")
    plt.plot(deployments, np.repeat(line2_results, 11), label="RPKI (full deployment)", linestyle="--")
    plt.legend()
    plt.xlabel("Deployment (top ISPs)")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure10(filename: str, nx_graph: nx.Graph, n_trials: int, tierOne: int):
    trials = uniform_random_trials(nx_graph, n_trials)

    # Set more detailed eval by setting steps smaller then 10
    deployments = np.arange(0, 110, 10)

    line1_results = []
    for deployment in deployments:
        print(f"ASPA Tier2 (deployment = {deployment})")
        line1_results.append(fmean(experiments.figure10_aspa(nx_graph, [deployment, 5], trials, tierOne)))
    line2_results = []
    for deployment in deployments:
        print(f"ASPA Tier2 (deployment = {deployment})")
        line2_results.append(fmean(experiments.figure10_aspa(nx_graph, [deployment, 10], trials, tierOne)))
    line3_results = []
    for deployment in deployments:
        print(f"ASPA Tier2 (deployment = {deployment})")
        line3_results.append(fmean(experiments.figure10_aspa(nx_graph, [deployment, 20], trials, tierOne)))
    line4_results = []
    for deployment in deployments:
        print(f"ASPA Tier2 (deployment = {deployment})")
        line4_results.append(fmean(experiments.figure10_aspa(nx_graph, [deployment, 30], trials, tierOne)))
    line5_results = []
    for deployment in deployments:
        print(f"ASPA Tier2 (deployment = {deployment})")
        line5_results.append(fmean(experiments.figure10_aspa(nx_graph, [deployment, 50], trials, tierOne)))
    line6_results = []
    for deployment in deployments:
        print(f"ASPA Tier2 (deployment = {deployment})")
        line6_results.append(fmean(experiments.figure10_aspa(nx_graph, [deployment, 80], trials, tierOne)))

    plt.figure(figsize=(10, 7))
    plt.plot(deployments, line1_results, label="Tier3: 5%")
    plt.plot(deployments, line2_results, label="Tier3: 10%")
    plt.plot(deployments, line3_results, label="Tier3: 20%")
    plt.plot(deployments, line4_results, label="Tier3: 30%")
    plt.plot(deployments, line5_results, label="Tier3: 50%")
    plt.plot(deployments, line6_results, label="Tier3: 80%")

    plt.legend()
    plt.xlabel("Deployment at percentage of Tier2 providers")
    plt.ylabel("Attacker's Success Rate (in %)")
    plt.savefig(filename)


def figure10_3d(filename: str, nx_graph: nx.Graph, n_trials: int):
    trials = uniform_random_trials(nx_graph, n_trials)

    deploymentsTierThree = np.arange(0, 101, 5)
    deploymentsTierTwo = np.arange(0, 101, 5)
    deploymentsTierOne = np.arange(0, 101, 5)

    line1_results = []
    for deployment in deploymentsTierThree:
        for deployment2 in deploymentsTierTwo:
            for deployment3 in deploymentsTierOne:
                print(f"ASPA deployment = {deployment3, deployment2, deployment})")
                line1_results.append(
                    fmean(experiments.figure10_aspa(nx_graph, [deployment, deployment2], trials, deployment3)))
        data_between = np.asarray(line1_results)
        np.savetxt(filename + '_backup' + str(deployment) + '.csv', data_between, delimiter=',')

    data = np.asarray(line1_results)
    np.savetxt(filename + '.csv', data, delimiter=',')

    print(line1_results)

    # eval.evaluate(data, filename, 10)


def figure_one_down_only(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_one(filename, nx_graph, n_trials, "DownOnly")


def figure_one_only_to_customer(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_one(filename, nx_graph, n_trials, "OTC")


# Increase deployment of down-only for each tier starting with tier one, finishing with tier three
# For each tier iteration, the previous tier(s) gets redeployed as well
# Steps: 1 %
def figure_roles_one(filename: str, nx_graph: nx.Graph, n_trials: int, algorithm: str):
    trials = uniform_random_trials(nx_graph, n_trials)
    start_time = time.time()
    deployments_tier_one = np.arange(0, 101, 5)
    deployments_tier_two = np.arange(0, 101, 5)
    # Thesis: Tier three has no effect 
    deployments_tier_three = np.arange(0, 101, 50)

    x_axes = []
    counter = 0
    result_tier_one = []
    result_tier_two = []
    result_tier_three = []
    result_attacker_success_rate = []

    for deployment_three in deployments_tier_three:
        for deployment_two in deployments_tier_two:
            for deployment_one in deployments_tier_one:
                counter += 1
                x_axes.append(counter)
                app = fmean(experiments.figure10_down_only_random(nx_graph, [deployment_three, deployment_two], trials,
                                                                  deployment_one, algorithm))
                result_attacker_success_rate.append(app)
                result_tier_one.append(deployment_one)
                result_tier_two.append(deployment_two)
                result_tier_three.append(deployment_three)
                print(deployment_one, ", ", deployment_two, ", ", deployment_three, ", ", app)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Elapsed time: ", elapsed_time)

    fig, ax1 = plt.subplots()
    ax1.set_xlabel('X-Axes')
    ax1.plot(x_axes, result_attacker_success_rate, label="Result Tier One", color='blue', linewidth=1.5)
    ax1.set_ylabel('Y-Axes (0.0 to 5.0)', color='blue')
    ax1.tick_params('y', colors='blue')

    ax2 = ax1.twinx()
    ax2.plot(x_axes, result_tier_one, label="Result Tier One", color='red')
    ax2.plot(x_axes, result_tier_two, label="Result Tier Two", color='green')
    ax2.plot(x_axes, result_tier_three, label="Result Tier Three", color='magenta')
    ax2.set_ylim(0, 100)
    ax2.tick_params('y', colors='red')

    plt.legend()
    plt.title('Increased deployment per tier.')
    plt.show()
    plt.savefig(filename)


def figure_two_down_only(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_2(filename, nx_graph, n_trials, "DownOnly")


def figure_two_only_to_customer(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_2(filename, nx_graph, n_trials, "OTC")


# Increase deployment of down-only for each tier starting with tier one, finishing with tier three
# Steps: 1 %
def figure_roles_2(filename: str, nx_graph: nx.Graph, n_trials: int, algorithm: str):
    trials = uniform_random_trials(nx_graph, n_trials)
    steps = 5
    deployments_tier_one = np.arange(0, 101, steps)
    deployments_tier_two = np.arange(0, 101, steps)
    deployments_tier_three = np.arange(0, 101, 50)

    for deployment_one in deployments_tier_one:
        app = fmean(experiments.figure10_down_only_random(nx_graph, [0, 0], trials, deployment_one, algorithm))
        print(deployment_one, ", ", 0, ", ", 0, ", ", app)

    for deployment_two in deployments_tier_two:
        app = fmean(experiments.figure10_down_only_random(nx_graph, [0, deployment_two], trials, 0, algorithm))
        print(0, ", ", deployment_two, ", ", 0, ", ", app)

    for deployment_three in deployments_tier_three:
        app = fmean(experiments.figure10_down_only_random(nx_graph, [deployment_three, 0], trials, 0, algorithm))
        print(0, ", ", 0, ", ", deployment_three, ", ", app)


def figure_three_down_only(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_3(filename, nx_graph, n_trials, "DownOnlyTopISP")


def figure_three_only_to_customer(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_3(filename, nx_graph, n_trials, "OTC_ISP")


# Select top ISPs
def figure_roles_3(filename: str, nx_graph: nx.Graph, n_trials: int, algorithm: str):
    print("Testing Figure 3")
    trials = uniform_random_trials(nx_graph, n_trials)
    steps = 10
    deployments_tier_one = np.arange(0, 101, steps)
    deployments_tier_two = np.arange(0, 101, steps)

    for deployment_one in deployments_tier_one:
        app = fmean(experiments.figure10_down_only_random(nx_graph, [0, 0], trials, deployment_one, algorithm))
        print(deployment_one, ", ", 0, ", ", 0, ", ", app)

    for deployment_two in deployments_tier_two:
        app = fmean(experiments.figure10_down_only_random(nx_graph, [0, deployment_two], trials, 0, algorithm))
        print(0, ", ", deployment_two, ", ", 0, ", ", app)


def figure_four_down_only(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_4(filename, nx_graph, n_trials, "DownOnlyTopISP")


def figure_four_only_to_customer(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_roles_4(filename, nx_graph, n_trials, "OTC_ISP")


# Select top ISPs
def figure_roles_4(filename: str, nx_graph: nx.Graph, n_trials: int, algorithm: str):
    print("Testing Figure 4")
    trials = uniform_random_trials(nx_graph, n_trials)
    steps = 10
    deployments_tier_one = np.arange(0, 101, steps)
    deployments_tier_two = np.arange(0, 101, steps)

    for deployment_two in deployments_tier_two:
        for deployment_one in deployments_tier_one:
            app = fmean(experiments.figure10_down_only_random(nx_graph, [0, deployment_two], trials, deployment_one,
                                                              algorithm))
            print(deployment_one, ", ", deployment_two, ", ", 0, ", ", app)


def deviation_figure(filename: str, nx_graph: nx.Graph, n_trials: int):
    result = []
    print("Trials: ", n_trials)
    iterations = 1000
    for i in range(iterations):
        progress = i / iterations
        progress_percent = int(progress * 100)
        progress_bar = "[" + "=" * progress_percent + " " * (100 - progress_percent) + "]"
        trials = uniform_random_trials(nx_graph, n_trials)
        current = fmean(experiments.figure10_down_only_random(nx_graph, [15, 20], trials, 25, "OTC_ISP"))
        result.append(current)
        print(f"\rProgress: {progress_bar} {progress_percent}% | Current_Result: {current}", end="", flush=True)
    std_deviation = np.std(result)
    mean_value = np.mean(result)
    variance = np.var(result)
    print('\n')
    print("Results: ", result)
    print("Data: ", std_deviation, mean_value, variance)
    print("#----------------------------------------------------------------------------#")


def figure_combined_random(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_down_only_and_aspa(filename, nx_graph, n_trials, "Combined")


def figure_combined_isp(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure_down_only_and_aspa(filename, nx_graph, n_trials, "Combined_ISP")


# Deploy ASPA and Down-Only at the same time
def figure_down_only_and_aspa(filename: str, nx_graph: nx.Graph, n_trials: int, algorithm: str):
    print("Running combined experiment.")
    trials = uniform_random_trials(nx_graph, n_trials)
    steps = 25
    deployments_tier_one = np.arange(0, 101, steps)
    deployments_tier_two = np.arange(0, 101, steps)
    deployments_tier_three = np.arange(0, 101, steps)
    for tier_two in deployments_tier_two:
        for tier_one in deployments_tier_one:
            for tier_two_aspa in deployments_tier_two:
                for tier_three_aspa in deployments_tier_three:
                    temporary_data = experiments.figure10_down_only_random(nx_graph, [0, tier_two], trials, tier_one,
                                algorithm, [0, tier_two_aspa, tier_three_aspa, 0, tier_two_aspa, tier_three_aspa])
                    app = fmean(temporary_data)
                    print("Deployment: ", [tier_one, tier_two, 0, 0, tier_two_aspa, tier_three_aspa], "; Result: ", app)

def figure10_100(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure10(filename, nx_graph, n_trials, 100)


def figure10_80(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure10(filename, nx_graph, n_trials, 80)


def figure10_50(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure10(filename, nx_graph, n_trials, 50)


def figure10_20(filename: str, nx_graph: nx.Graph, n_trials: int):
    figure10(filename, nx_graph, n_trials, 20)


# ASPA Selection Strategy: Random object creation, random policy assignment
def figure11(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()
    # trials = route_leak_trials(nx_graph, n_trials)
    trials = uniform_random_trials(nx_graph, n_trials)
    # attacker_sample = find_asyss_with_repetition(nx_graph, 3, n_trials)
    # print('Attackers: ', attacker_sample)
    # trials = trials_with_predefined_attackers(nx_graph, n_trials, attacker_sample)
    # trials = [('4267', '132770')]

    ASPA_object_deployment = np.arange(0, 101, 1)
    ASPA_policy_deployment = np.arange(0, 101, 1)
    ASPA_results = np.zeros((101, 101))

    # Fill numpy array with results
    for ASPA_objects_index in ASPA_object_deployment:
        for ASPA_policy_index in ASPA_policy_deployment:
            ASPA_results[ASPA_objects_index][ASPA_policy_index] = fmean(
                experiments.figure11_random_aspa_deployment(nx_graph, ASPA_objects_index, ASPA_policy_index, trials))
            print('Object deployment: ' + str(ASPA_objects_index) + '%; Policy Deployment: ' + str(
                ASPA_policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  ASPA_results[ASPA_objects_index][ASPA_policy_index])

    # Save results for later processing:
    np.save(filename, ASPA_results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(ASPA_policy_deployment, [i] * 101, c=ASPA_results[i], s=[1.0] * 101, alpha=1, cmap=cmap)

    plt.colorbar();  # show color scale
    plt.xlabel("ASPA policy deployment \n (random selection)")
    plt.ylabel("ASPA object deployment \n (random selection)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASPA Selection Strategy: top-to-bottom object creation, top-to-bottom policy assignment
def figure12(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    ASPA_object_deployment = np.arange(0, 101, 1)
    ASPA_policy_deployment = np.arange(0, 101, 1)
    ASPA_results = np.zeros((101, 101))

    # Fill numpy array with results
    for ASPA_objects_index in ASPA_object_deployment:
        for ASPA_policy_index in ASPA_policy_deployment:
            ASPA_results[ASPA_objects_index][ASPA_policy_index] = fmean(
                experiments.figure12_selective_aspa_deployment(nx_graph, ASPA_objects_index, ASPA_policy_index, trials))
            print('Object deployment: ' + str(ASPA_objects_index) + '%; Policy Deployment: ' + str(
                ASPA_policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  ASPA_results[ASPA_objects_index][ASPA_policy_index])

    # print(ASPA_results)

    np.save(filename, ASPA_results)  # Save numpy array for later use

    indices = np.arange(0, 101, 1)

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    plt.figure(figsize=(10, 8))
    for i in range(101):
        plt.scatter(indices, [i] * 101, c=ASPA_results[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    plt.colorbar();  # show color scale
    plt.xlabel("ASPA policy deployment \n (TopToBottom Deployment)")
    plt.ylabel("ASPA object deployment \n (TopToBottom Deployment)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# Standard Deviation
# We do not deploy any ASPA objects or policy. We only want to know the deviation between runs.
# This figure creates three box-plots, 10,100, and 1000 trials and shows the mean and standard deviation.

# TODO: Start this figure without any SEED parameter - otherwise all trials will be the same!!
def figure13(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()  # 15 hours processing time for 10,100,1000
    # Times for a single run with 250 CPU available:
    # 10 trials: 5.3 sec
    # 100 trials: 12.2 sec
    # 1000 trials: 30.7 sec
    # 10000 trials: 242 sec
    # Total time: roughly 4 days

    print('Started trials with 10')
    results_10 = []
    for i in range(1000):
        print('10 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 10)
        results_10.append(fmean(experiments.figure12_selective_aspa_deployment(nx_graph, 0, 0, trials)))

    print('Started trials with 100')
    results_100 = []
    for i in range(1000):
        print('100 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 100)
        results_100.append(fmean(experiments.figure12_selective_aspa_deployment(nx_graph, 0, 0, trials)))

    print('Started trials with 1.000')
    results_1000 = []
    for i in range(1000):
        print('1.000 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 1000)
        results_1000.append(fmean(experiments.figure12_selective_aspa_deployment(nx_graph, 0, 0, trials)))

    print('Started trials with 10.000')
    results_10000 = []
    for i in range(1000):
        print('10.000 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 10000)
        results_10000.append(fmean(experiments.figure12_selective_aspa_deployment(nx_graph, 0, 0, trials)))

    overall_results = np.array([results_10, results_100, results_1000, results_10000])

    np.save(filename, overall_results)  # Save numpy array for later use
    # data = np.load(filename + '.npy') # Load numpy array

    end = timer()
    print(timedelta(seconds=end - start))

    ten_trials_mean = np.mean(overall_results[0])
    hundred_trials_mean = np.mean(overall_results[1])
    thousand_trials_mean = np.mean(overall_results[2])
    tenthousand_trials_mean = np.mean(overall_results[3])

    ten_trials_std = np.std(overall_results[0])
    hundred_trials_std = np.std(overall_results[1])
    thousand_trials_std = np.std(overall_results[2])
    tenthousand_trials_std = np.std(overall_results[3])

    print('Means: ', ten_trials_mean, hundred_trials_mean, thousand_trials_mean, tenthousand_trials_mean)
    print('Deviations: ', ten_trials_std, hundred_trials_std, thousand_trials_std, tenthousand_trials_std)

    # Creating plot
    data = [overall_results[0], overall_results[1], overall_results[2], overall_results[3]]
    fig, ax = plt.subplots(figsize=(5, 9))

    # Creating axes instance
    bp = ax.boxplot(data, patch_artist=True, notch='True', vert=1, widths=0.8)

    colors = ['#0000FF', '#00FF00', '#FFFF00']

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#8B008B',
                    linewidth=1.5,
                    linestyle=":")

    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color='#8B008B',
                linewidth=2)

    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color='red',
                   linewidth=3)

    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker='D',
                  color='#e7298a',
                  alpha=0.5)

    # Adding title
    ax.set_title("Mean and standard deviation \n for different number of trials")
    ax.set_ylabel('Route leak success rate [%]')
    plt.xlabel("Number of trials")

    # Removing top axes and right axes
    # ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

    plt.xticks([1, 2, 3, 4], ['10', '100', '1.000', '10.000'])

    fig.subplots_adjust(hspace=0.1)
    plt.ylim(0, 3)

    # show plot
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()
    print(timedelta(seconds=end - start))


# ASPA Selection Strategy: bottom-to-top object creation, top-to-bottom policy assignment
def figure14(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    ASPA_object_deployment = np.arange(0, 101, 1)
    ASPA_policy_deployment = np.arange(0, 101, 1)
    ASPA_results = np.zeros((101, 101))

    # Fill numpy array with results
    for ASPA_objects_index in ASPA_object_deployment:
        for ASPA_policy_index in ASPA_policy_deployment:
            ASPA_results[ASPA_objects_index][ASPA_policy_index] = fmean(
                experiments.figure14_selective_aspa_deployment(nx_graph, ASPA_objects_index, ASPA_policy_index, trials))
            print('Object deployment: ' + str(ASPA_objects_index) + '%; Policy Deployment: ' + str(
                ASPA_policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  ASPA_results[ASPA_objects_index][ASPA_policy_index])

    # print(ASPA_results)

    np.save(filename, ASPA_results)  # Save numpy array for later use
    # data = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    plt.figure(figsize=(10, 8))
    for i in range(101):
        plt.scatter(ASPA_object_deployment, [i] * 101, c=ASPA_results[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    plt.colorbar();  # show color scale
    plt.xlabel("ASPA policy deployment \n (TopToBottom Deployment)")
    plt.ylabel("ASPA object deployment \n (BottomToTop Deployment)")

    # plt.show()
    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASPA Selection Strategy: top-to-bottom object creation, top-to-bottom policy assignment
# Since we only get interesting findings in the 20x20 lower left of Figure12, we zoom in and make deployment more fine-grained.
def figure15(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    ASPA_object_deployment = np.round(np.arange(0, 20.1, 0.2), decimals=1)  # Adjusted to 0- 20 % deployment!
    ASPA_policy_deployment = np.round(np.arange(0, 20.1, 0.2), decimals=1)  # Adjusted to 0- 20 % deployment!
    ASPA_object_deployment_positions = np.arange(0, 101, 1)  # Needed for indexing
    ASPA_policy_deployment_positions = np.arange(0, 101, 1)  # Needed for indexing
    ASPA_results = np.zeros((101, 101))

    # Fill numpy array with results
    for ASPA_objects_deployment_position in ASPA_object_deployment_positions:
        ASPA_objects_index = ASPA_object_deployment[ASPA_objects_deployment_position]
        for ASPA_policy_deployment_position in ASPA_policy_deployment_positions:
            ASPA_policy_index = ASPA_policy_deployment[ASPA_policy_deployment_position]
            ASPA_results[ASPA_objects_deployment_position][ASPA_policy_deployment_position] = fmean(
                experiments.figure12_selective_aspa_deployment(nx_graph, ASPA_objects_index, ASPA_policy_index, trials))
            print('Object deployment: ' + str(ASPA_objects_index) + '%; Policy Deployment: ' + str(
                ASPA_policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  ASPA_results[ASPA_objects_deployment_position][ASPA_policy_deployment_position])

    # print(ASPA_results)

    np.save(filename, ASPA_results)  # Save numpy array for later use
    # data = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(ASPA_policy_deployment_positions, [i] * 101, c=ASPA_results[i], s=[1.0] * 101, alpha=1, cmap=cmap)

    plt.colorbar();  # show color scale
    plt.xlabel("ASPA policy deployment \n (Top-to-bottom selection)")
    plt.ylabel("ASPA object deployment \n (Top-to-bottom selection)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASPA Selection Strategy: top-to-bottom object creation, top-to-bottom policy assignment
# Since we only get interesting findings in the 30x30 lower left of Figure12, we zoom in and make deployment more fine-grained.
def figure16(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    ASPA_object_deployment = np.round(np.arange(0, 30.1, 0.3), decimals=1)  # Adjusted to 0- 30 % deployment!
    ASPA_policy_deployment = np.round(np.arange(0, 30.1, 0.3), decimals=1)  # Adjusted to 0- 30 % deployment!
    ASPA_object_deployment_positions = np.arange(0, 101, 1)  # Needed for indexing
    ASPA_policy_deployment_positions = np.arange(0, 101, 1)  # Needed for indexing
    ASPA_results = np.zeros((101, 101))

    # Fill numpy array with results
    for ASPA_objects_deployment_position in ASPA_object_deployment_positions:
        ASPA_objects_index = ASPA_object_deployment[ASPA_objects_deployment_position]
        for ASPA_policy_deployment_position in ASPA_policy_deployment_positions:
            ASPA_policy_index = ASPA_policy_deployment[ASPA_policy_deployment_position]
            ASPA_results[ASPA_objects_deployment_position][ASPA_policy_deployment_position] = fmean(
                experiments.figure12_selective_aspa_deployment(nx_graph, ASPA_objects_index, ASPA_policy_index, trials))
            print('Object deployment: ' + str(ASPA_objects_index) + '%; Policy Deployment: ' + str(
                ASPA_policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  ASPA_results[ASPA_objects_deployment_position][ASPA_policy_deployment_position])

    # print(ASPA_results)

    np.save(filename, ASPA_results)  # Save numpy array for later use
    # data = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(ASPA_policy_deployment_positions, [i] * 101, c=ASPA_results[i], s=[1.0] * 101, alpha=1, cmap=cmap)

    plt.colorbar();  # show color scale
    plt.xlabel("ASPA policy deployment \n (Top-to-bottom selection)")
    plt.ylabel("ASPA object deployment \n (Top-to-bottom selection)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASPA Selection Strategy: bottom-to-top object creation, top-to-bottom policy assignment
# Since we only get interesting findings in the 5x100 upper part of Figure14, we zoom in and make deployment more fine-grained.
def figure17(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    ASPA_object_deployment = np.round(np.arange(95, 100.05, 0.05), decimals=2)  # Adjusted to 95 - 100 % deployment!
    ASPA_policy_deployment = np.round(np.arange(0, 101, 1), decimals=1)  # Adjusted to 0- 20 % deployment!
    ASPA_object_deployment_positions = np.arange(0, 101, 1)  # Needed for indexing
    ASPA_policy_deployment_positions = np.arange(0, 101, 1)  # Needed for indexing
    ASPA_results = np.zeros((101, 101))

    # Fill numpy array with results
    for ASPA_objects_deployment_position in ASPA_object_deployment_positions:
        ASPA_objects_index = ASPA_object_deployment[ASPA_objects_deployment_position]
        for ASPA_policy_deployment_position in ASPA_policy_deployment_positions:
            ASPA_policy_index = ASPA_policy_deployment[ASPA_policy_deployment_position]
            ASPA_results[ASPA_objects_deployment_position][ASPA_policy_deployment_position] = fmean(
                experiments.figure14_selective_aspa_deployment(nx_graph, ASPA_objects_index, ASPA_policy_index, trials))
            print('Object deployment: ' + str(ASPA_objects_index) + '%; Policy Deployment: ' + str(
                ASPA_policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  ASPA_results[ASPA_objects_deployment_position][ASPA_policy_deployment_position])

    # print(ASPA_results)

    np.save(filename, ASPA_results)  # Save numpy array for later use
    # data = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(ASPA_policy_deployment_positions, [i] * 101, c=ASPA_results[i], s=[1.0] * 101, alpha=1, cmap=cmap,
                    norm=norm)

    plt.colorbar();  # show color scale
    plt.xlabel("ASPA policy deployment \n (Top-to-bottom selection)")
    plt.ylabel("ASPA object deployment \n (Bottom-to-top selection)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASCones Selection Strategy: Random object creation, random policy assignment
def figure30(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()
    # trials = route_leak_trials(nx_graph, n_trials)
    trials = uniform_random_trials(nx_graph, n_trials)
    # attacker_sample = find_asyss_with_repetition(nx_graph, 3, n_trials)
    # print('Attackers: ', attacker_sample)
    # trials = trials_with_predefined_attackers(nx_graph, n_trials, attacker_sample)
    # trials = [('4267', '132770')]

    object_deployment = np.arange(0, 101, 20)
    policy_deployment = np.arange(0, 101, 20)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure30_random_ascones_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(policy_deployment, [i] * 101, c=results[i], s=[1.0] * 101, alpha=1, cmap=cmap)

    plt.colorbar();  # show color scale
    plt.xlabel("ASCONES policy deployment \n (random selection)")
    plt.ylabel("ASCONES object deployment \n (random selection)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASCONES Selection Strategy: top-to-bottom object creation, top-to-bottom policy assignment
def figure31(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure31_selective_ascones_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(policy_deployment, [i] * 101, c=results[i], s=[1.0] * 101, alpha=1, cmap=cmap)

    plt.colorbar();  # show color scale
    plt.xlabel("ASCONES policy deployment \n (Selection TopToBottom)")
    plt.ylabel("ASCONES object deployment \n (Selection TopToBottom)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# ASCONES Selection Strategy: bottom-to-top object creation, top-to-bottom policy assignment
def figure32(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure32_selective_ascones_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])

    plt.figure(figsize=(10, 8))
    for i in range(101):
        if i == 0:
            continue  # There seems to be a bug that the first line is green although values should assign the color red
        plt.scatter(policy_deployment, [i] * 101, c=results[i], s=[1.0] * 101, alpha=1, cmap=cmap)

    plt.colorbar();  # show color scale
    plt.title('With 74k ASes on x axis and 11k ASes on y axis')
    plt.xlabel("ASCONES policy deployment \n (Selection TopToBottom)")
    plt.ylabel("ASCONES object deployment \n (Selection BottomToTop)")
    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# Path manipulation attack - Forged-origin prefix hijack with ASPA protection (random objects and policy deployment)
def figure40(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure40_random_aspa_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    indices = np.arange(0, 101, 1)

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5, 4))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=results[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(12)

    plt.rc('font', size=12)  # controls default text sizes

    plt.xticks([0, 20, 40, 60, 80, 100], ['0', '15', '30', '45', '60', '74.1'])
    plt.yticks([0, 20, 40, 60, 80, 100], ['0', '15', '30', '45', '60', '74.1'])
    ax.yaxis.labelpad = -1  # margin of x-label
    ax.xaxis.labelpad = 4  # margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment [# ASes in k]")

    # plt.plot(get_rpki_history()[1], get_rpki_history()[0], linestyle='--', color='black')
    # rpki_start_date = date(2012, 7, 1)  # ROA start date
    # rpki_start_date = date(2019, 9, 18) #ROV start date
    # a = ax.plot(get_rpki_history(rpki_start_date)[1][:], get_rpki_history(rpki_start_date)[0][:], linestyle='solid', color='cyan', label='RPKI projection', linewidth=3)
    # b = ax.plot(get_rpki_history(rpki_start_date)[1][2550:], get_rpki_history(rpki_start_date)[0][2550:]-18.5, linestyle='--', color='blue', label='Accelerated RPKI projection')
    plt.ylim(-5, 105)

    # leg = ax.legend([a,b], ['Original RPKI projection', 'Accelerated RPKI projection'], loc="lower right")
    leg = ax.legend(loc="lower right")
    # leg.legendHandles[0].set_color('black')
    # leg.legendHandles[1].set_color('blue')

    # Get the bounding box of the original legend
    bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())

    # Change to location of the legend.
    xOffset = -0.02
    yOffset = 0.05
    bb.x0 += xOffset
    bb.x1 += xOffset
    bb.y0 += yOffset
    bb.y1 += yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# TODO: Start this figure without any SEED parameter - otherwise all trials will be the same!!
def figure41(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    print('Started trials with 10')
    results_10 = []
    for i in range(1000):
        print('10 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 10)
        results_10.append(fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials)))

    print('Started trials with 100')
    results_100 = []
    for i in range(1000):
        print('100 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 100)
        results_100.append(fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials)))

    print('Started trials with 1.000')
    results_1000 = []
    for i in range(1000):
        print('1.000 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 1000)
        results_1000.append(fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials)))

    print('Started trials with 10.000')
    results_10000 = []
    for i in range(1000):
        print('10.000 trials, Run: ', i)
        trials = uniform_random_trials(nx_graph, 10000)
        results_10000.append(fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials)))

    # overall_results = np.array([results_10, results_100, results_1000, results_10000])
    overall_results = np.array([results_10, results_100, results_1000, results_10000])

    np.save(filename, overall_results)  # Save numpy array for later use
    # data = np.load(filename + '.npy') # Load numpy array


# Path manipulation attack - Forged-origin prefix hijack with ASPA protection - Objects TopToBottom, Policy TopToBottom Selection Strategy
def figure42(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)
    # print(trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure42_selective_aspa_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    indices = np.arange(0, 101, 1)

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5, 4))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=results[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(12)

    plt.rc('font', size=12)  # controls default text sizes

    plt.xticks([0, 20, 40, 60, 80, 100], ['0', '15', '30', '45', '60', '74.1'])
    plt.yticks([0, 20, 40, 60, 80, 100], ['0', '15', '30', '45', '60', '74.1'])
    ax.yaxis.labelpad = -1  # margin of x-label
    ax.xaxis.labelpad = 4  # margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment [# ASes in k]")

    # plt.plot(get_rpki_history()[1], get_rpki_history()[0], linestyle='--', color='black')
    # rpki_start_date = date(2012, 7, 1)  # ROA start date
    # rpki_start_date = date(2019, 9, 18) #ROV start date
    # a = ax.plot(get_rpki_history(rpki_start_date)[1][:], get_rpki_history(rpki_start_date)[0][:], linestyle='solid', color='cyan', label='RPKI projection', linewidth=3)
    # b = ax.plot(get_rpki_history(rpki_start_date)[1][2550:], get_rpki_history(rpki_start_date)[0][2550:]-18.5, linestyle='--', color='blue', label='Accelerated RPKI projection')
    plt.ylim(-5, 105)

    # leg = ax.legend([a,b], ['Original RPKI projection', 'Accelerated RPKI projection'], loc="lower right")
    leg = ax.legend(loc="lower right")
    # leg.legendHandles[0].set_color('black')
    # leg.legendHandles[1].set_color('blue')

    # Get the bounding box of the original legend
    bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())

    # Change to location of the legend.
    xOffset = -0.02
    yOffset = 0.05
    bb.x0 += xOffset
    bb.x1 += xOffset
    bb.y0 += yOffset
    bb.y1 += yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# Path manipulation attack - Forged-origin prefix hijack with ASPA protection - Objects BottomToTop, Policy TopToBottom Selection Strategy
def figure43(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure43_selective_aspa_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use
    # ASPA_results = np.load(filename + '.npy') # Load numpy array

    indices = np.arange(0, 101, 1)

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5, 4))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=results[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(12)

    plt.rc('font', size=12)  # controls default text sizes

    plt.xticks([0, 20, 40, 60, 80, 100], ['0', '15', '30', '45', '60', '74.1'])
    plt.yticks([0, 20, 40, 60, 80, 100], ['0', '15', '30', '45', '60', '74.1'])
    ax.yaxis.labelpad = -1  # margin of x-label
    ax.xaxis.labelpad = 4  # margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment [# ASes in k]")

    # plt.plot(get_rpki_history()[1], get_rpki_history()[0], linestyle='--', color='black')
    # rpki_start_date = date(2012, 7, 1)  # ROA start date
    # rpki_start_date = date(2019, 9, 18) #ROV start date
    # a = ax.plot(get_rpki_history(rpki_start_date)[1][:], get_rpki_history(rpki_start_date)[0][:], linestyle='solid', color='cyan', label='RPKI projection', linewidth=3)
    # b = ax.plot(get_rpki_history(rpki_start_date)[1][2550:], get_rpki_history(rpki_start_date)[0][2550:]-18.5, linestyle='--', color='blue', label='Accelerated RPKI projection')
    plt.ylim(-5, 105)

    # leg = ax.legend([a,b], ['Original RPKI projection', 'Accelerated RPKI projection'], loc="lower right")
    leg = ax.legend(loc="lower right")
    # leg.legendHandles[0].set_color('black')
    # leg.legendHandles[1].set_color('blue')

    # Get the bounding box of the original legend
    bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())

    # Change to location of the legend.
    xOffset = -0.02
    yOffset = 0.05
    bb.x0 += xOffset
    bb.x1 += xOffset
    bb.y0 += yOffset
    bb.y1 += yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    # plt.show()

    plt.savefig(filename + '.svg', format="svg")

    end = timer()

    print(timedelta(seconds=end - start))


# Path manipulation attack - Forged-origin prefix hijack with ASPA protection - Objects TopToBottom, Policy BottomToTop Selection Strategy
def figure44(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)
    # print(trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure44_selective_aspa_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use

    end = timer()
    print(timedelta(seconds=end - start))


# Path manipulation attack - Forged-origin prefix hijack with ASPA protection - Objects BottomToTop, Policy BottomToTop Selection Strategy
def figure45(filename: str, nx_graph: nx.Graph, n_trials: int):
    start = timer()

    trials = uniform_random_trials(nx_graph, n_trials)
    # print(trials)

    object_deployment = np.arange(0, 101, 1)
    policy_deployment = np.arange(0, 101, 1)
    results = np.zeros((101, 101))

    # Fill numpy array with results
    for objects_index in object_deployment:
        for policy_index in policy_deployment:
            results[objects_index][policy_index] = fmean(
                experiments.figure45_selective_aspa_deployment(nx_graph, objects_index, policy_index, trials))
            print('Object deployment: ' + str(objects_index) + '%; Policy Deployment: ' + str(
                policy_index) + '%; Averaged attacker success rate over ' + str(n_trials) + ' trial runs: ',
                  results[objects_index][policy_index])

    # Save results for later processing:
    np.save(filename, results)  # Save numpy array for later use

    end = timer()
    print(timedelta(seconds=end - start))


# This function prints the results for 0%object and 0% policy ASPA deployment to find a correct seed that is within the mean identified in the deviations figure.
def find_seed_routeleak(filename: str, nx_graph: nx.Graph, n_trials: int):
    print(
        'ASPA Object and Policy deployment for each run is 0%. Results show the bare graph and the ratio for leaked routes.')
    # print('Number of trials in each run: ', n_trials)
    for seed in range(100):
        random.seed(seed)
        trials10 = uniform_random_trials(nx_graph, 10)
        random.seed(seed)
        trials100 = uniform_random_trials(nx_graph, 100)
        random.seed(seed)
        trials1000 = uniform_random_trials(nx_graph, 1000)
        result10 = fmean(experiments.figure11_random_aspa_deployment(nx_graph, 0, 0, trials10))
        result100 = fmean(experiments.figure11_random_aspa_deployment(nx_graph, 0, 0, trials100))
        result1000 = fmean(experiments.figure11_random_aspa_deployment(nx_graph, 0, 0, trials1000))
        print("Seed: " + str(seed) + " and the follwing % of AS Graph had leaked route in their RIB: ")
        print('10 Trials: ', result10)
        print('100 Trials: ', result100)
        print('1000 Trials: ', result1000)
        print('-----------')
        print('')
    # For 1000 trials:
    # Seed: 0 and Result: 1.19312462634154
    # Seed: 1 and Result: 1.1094031061235412
    # Seed: 2 and Result: 1.229537569421176
    # Seed: 3 and Result: 1.254220298543766
    # Seed: 4 and Result: 1.1709700508162113
    # Seed: 5 and Result: 1.2559283743268548
    # Seed: 6 and Result: 1.0139273688733321
    # Seed: 7 and Result: 1.3072537941073283
    # Seed: 8 and Result: 1.0062359678771418


# This function prints the results for 0%object and 0% policy ASPA deployment to find a correct seed that is within the mean identified in the deviations figure.
def find_seed_hijacking(filename: str, nx_graph: nx.Graph, n_trials: int):
    print(
        'ASPA Object and Policy deployment for each run is 0%. Results show the bare graph and the ratio for leaked routes.')
    # print('Number of trials in each run: ', n_trials)
    for seed in range(100):
        random.seed(seed)
        trials10 = uniform_random_trials(nx_graph, 10)
        random.seed(seed)
        trials100 = uniform_random_trials(nx_graph, 100)
        random.seed(seed)
        trials1000 = uniform_random_trials(nx_graph, 1000)
        result10 = fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials10))
        result100 = fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials100))
        result1000 = fmean(experiments.figure40_random_aspa_deployment(nx_graph, 0, 0, trials1000))
        print("Seed: " + str(seed) + " and the follwing % of AS Graph had leaked route in their RIB: ")
        print('10 Trials: ', result10)
        print('100 Trials: ', result100)
        print('1000 Trials: ', result1000)
        print('-----------')
        print('')


def fmean(vals: Sequence[Fraction]) -> float:
    return float(statistics.mean(vals))


def random_pair(as_ids: List[AS_ID]) -> Tuple[AS_ID, AS_ID]:
    [asn1, asn2] = random.sample(as_ids, 2)
    return (asn1, asn2)
