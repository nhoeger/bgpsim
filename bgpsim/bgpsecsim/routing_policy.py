from typing import Callable, Generator

import random
# from bgpsecsim.asys import Relation, Route, RoutingPolicy
from bgpsecsim.asys import Relation, Route, RoutingPolicy


class DefaultPolicy(RoutingPolicy):
    def __init__(self):
        self.name = 'DefaultPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        # not in combination with return, inverts the value
        return not route.contains_cycle()
        # If Route contains a cycle, then it returns true
        # -> the not inverts the bool and so the Route is declined as there is a cycle in it

    def prefer_route(self, current: Route, new: Route) -> bool:
        # assert triggers error as soon as condition is false, in this case, if both final AS aren't the same
        assert current.final == new.final, "routes must have same final AS"

        for rule in self.preference_rules():
            current_val = rule(current)
            new_val = rule(new)

            if current_val is not None:
                if new_val is not None:
                    if current_val < new_val:
                        return False
                    if new_val < current_val:
                        return True

        return False

    def forward_to(self, route: Route, relation: Relation) -> bool:
        asys = route.final
        first_hop_rel = asys.get_relation(route.first_hop)
        assert first_hop_rel is not None

        # Route is forwarded either if was received by a customer or if it is going to be sent to a customer.
        return first_hop_rel == Relation.CUSTOMER or relation == Relation.CUSTOMER

    # Generators are iterators, a kind of iterable you can only iterate over once.
    # Generators do not store all the values in memory, they generate the values on the fly:
    def preference_rules(self) -> Generator[Callable[[Route], int], None, None]:
        # 1. Local preferences
        def local_pref(route):
            relation = route.final.get_relation(route.first_hop)
            return relation.value if relation else -1

        yield local_pref
        # 2. AS-path length
        yield lambda route: route.length
        # 3. Next hop AS number
        yield lambda route: route.first_hop.as_id


class RPKIPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'RPKIPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        return super().accept_route(route) and not route.origin_invalid


class PathEndValidationPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'PathEndValidationPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        return super().accept_route(route) and not route.path_end_invalid


class BGPsecHighSecPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'BGPsecHighSecPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        # Rule should actually be to reject unauthenticated routes if all ASs on it have
        # bgp_sec_enabled, but that is less convenient in our simulation.
        return super().accept_route(route) and not route.origin_invalid

    # Lambda takes several arguments, but only has one expression
    def preference_rules(self) -> Generator[Callable[[Route], int], None, None]:
        # Prefer authenticated routes
        yield lambda route: not route.authenticated

        # 1. Local preferences
        def local_pref(route):
            relation = route.final.get_relation(route.first_hop)
            return relation.value if relation else -1

        yield local_pref
        # 2. AS-path length
        yield lambda route: route.length
        # 3. Next hop AS number
        yield lambda route: route.first_hop.as_id


class BGPsecMedSecPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'BGPsecMedSecPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        # Rule should actually be to reject unauthenticated routes if all ASs on it have
        # bgp_sec_enabled, but that is less convenient in our simulation.
        return super().accept_route(route) and not route.origin_invalid

    def preference_rules(self) -> Generator[Callable[[Route], int], None, None]:
        # 1. Local preferences
        def local_pref(route):
            relation = route.final.get_relation(route.first_hop)
            return relation.value if relation else -1

        yield local_pref
        # Prefer authenticated routes
        yield lambda route: not route.authenticated
        # 2. AS-path length
        yield lambda route: route.length
        # 3. Next hop AS number
        yield lambda route: route.first_hop.as_id


class BGPsecLowSecPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'BGPsecLowSecPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        # Rule should actually be to reject unauthenticated routes if all ASs on it have
        # bgp_sec_enabled, but that is less convenient in our simulation.
        return super().accept_route(route) and not route.origin_invalid

    def preference_rules(self) -> Generator[Callable[[Route], int], None, None]:
        # 1. Local preferences
        def local_pref(route):
            relation = route.final.get_relation(route.first_hop)
            return relation.value if relation else -1

        yield local_pref
        # 2. AS-path length
        yield lambda route: route.length
        # Prefer authenticated routes
        yield lambda route: not route.authenticated
        # 3. Next hop AS number
        yield lambda route: route.first_hop.as_id


# Rules are all the same for RouteLeakPolicy and DefaultPolicy, except that RouteLeakPolicy forwards routes to any peer.
class RouteLeakPolicy(RoutingPolicy):
    def __init__(self):
        self.name = 'RouteLeakPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        # not in combination with return, inverts the value
        return not route.contains_cycle()
        # If Route contains a cycle, then it returns true
        # -> the not inverts the bool and so the Route is declined as there is a cycle in it

    def prefer_route(self, current: Route, new: Route) -> bool:
        # assert triggers error as soon as condition is false, in this case, if both final AS aren't the same
        assert current.final == new.final, "routes must have same final AS"

        for rule in self.preference_rules():
            current_val = rule(current)
            new_val = rule(new)

            if current_val is not None:
                if new_val is not None:
                    if current_val < new_val:
                        return False
                    if new_val < current_val:
                        return True

        return False

    def forward_to(self, route: Route, relation: Relation) -> bool:
        #        asys = route.final
        #        first_hop_rel = asys.get_relation(route.first_hop)
        #        assert first_hop_rel is not None
        return True  # Forward route to any peer regardless of relationship (not respecting Gao-Rexford model, hence constituting a RouteLeak).

    # Generators are iterators, a kind of iterable you can only iterate over once.
    # Generators do not store all the values in memory, they generate the values on the fly:
    def preference_rules(self) -> Generator[Callable[[Route], int], None, None]:
        # 1. Local preferences
        def local_pref(route):
            relation = route.final.get_relation(route.first_hop)
            return relation.value if relation else -1

        yield local_pref
        # 2. AS-path length
        yield lambda route: route.length
        # 3. Next hop AS number
        yield lambda route: route.first_hop.as_id


def perform_ASPA_algorithm(route):
    result = False
    # We do not implement the mandatory check in Section 6 of the draft for intentionally leaked ASes that removed their ASN from the path as we do not resemble this use case here.
    # Algorithm for upstream paths (routes received by customer), Section 6.1 of draft
    # print(route)

    relation = route.final.get_relation(route.first_hop)
    if relation == Relation.CUSTOMER or relation == Relation.PEER:
        # print('')
        # print('-------')
        # print('Relation: ', relation)
        # print('Route: ', route)
        # Step1 - If the AS_PATH has an AS_SET, then the procedure halts with the outcome "Invalid".
        # Step2 - Collapse prepends in the AS_SEQUENCE(s) in the AS_PATH (i.e., keep only the unique AS numbers). Let the resulting ordered sequence be represented by {AS(N), AS(N-1), ..., AS(2), AS(1)}, where AS(1) is the first-added (i.e., origin) AS and AS(N) is the last-added AS and neighbor to the receiving/validating AS.
        # Step3 - If N = 1, then the procedure halts with the outcome "Valid". Else, continue.
        if len(route.path) < 2:  # case never happens
            raise Exception('Route length below verifyable!')
        elif len(route.path) == 2:  # the route object also contains the AS that currently validates as destination
            result = 'Valid'
        # Step4 - At this step, N ≥ 2. If there is an i such that 2 ≤ i ≤ N and hop(AS(i-1), AS(i)) = "Not Provider+", then the procedure halts with the outcome "Invalid". Else, continue.
        # Step5 - If there is an i such that 2 ≤ i ≤ N and hop(AS(i-1), AS(i)) = "No Attestation", then the procedure halts with the outcome "Unknown". Else, the procedure halts with the outcome "Valid".
        else:
            result = 'Valid'
            for i, curr_asys in enumerate(route.path):
                if i + 2 < len(
                        route.path):  # Verifying AS contained in route AND hop towards verifying AS is known and not checked in ASPA algorithm
                    next_asys = route.path[i + 1]
                    # print('Curr AS: ', curr_asys.as_id)
                    # print('Curr AS ASPA', curr_asys.aspa)
                    # print('Next AS: ', next_asys.as_id)
                    if curr_asys.aspa != None and not next_asys.as_id in curr_asys.aspa[
                        1]:  # ASPA present but upstream not contained in provider list
                        # Invalid
                        result = 'Invalid'
                        break
                    elif curr_asys.aspa == None:  # ASPA not present
                        # No attestation
                        result = 'Unknown'
                        break
                    else:
                        # ASPA object present and current AS authorized its upstream
                        pass

    elif relation == Relation.PROVIDER:
        # print('')
        # print('-------')
        # print('Relation: ', relation)
        # print('Route: ', route)
        # Step1 - If the AS_PATH has an AS_SET, then the procedure halts with the outcome "Invalid".
        # Step2 - Collapse prepends in the AS_SEQUENCE(s) in the AS_PATH (i.e., keep only the unique AS numbers). Let the resulting ordered sequence be represented by {AS(N), AS(N-1), ..., AS(2), AS(1)}, where AS(1) is the first-added (i.e., origin) AS and AS(N) is the last-added AS and neighbor to the receiving/validating AS.
        # Step3 - If 1 ≤ N ≤ 2, then the procedure halts with the outcome "Valid". Else, continue.
        if len(route.path) < 2:  # case never happens
            raise Exception('Route length below verifyable!')
        elif len(route.path) == 2 or len(
                route.path) == 3:  # the route object also contains the AS that currently validates as destination
            # Length 2: This case covers an upstream sending a route directly.
            # Length 3: This case covers essentially three scenarios. The upstream of the verifying AS receives the route either from a customer, a peer, or it's upstream. All trivially valid cases.
            result = 'Valid'
        else:  # For paths > 3
            # Step4 - At this step, N ≥ 3.  Given the above-mentioned ordered sequence,
            #        find the lowest value of u (2 ≤ u ≤ N) for which hop(AS(u-1),
            #        AS(u)) = "Not Provider+".  Call it u_min.  If no such u_min
            #        exists, set u_min = N+1.  Find the highest value of v (N-1 ≥ v ≥
            #        1) for which hop(AS(v+1), AS(v)) = "Not Provider+".  Call it
            #        v_max.  If no such v_max exists, then set v_max = 0.  If u_min ≤
            #        v_max, then the procedure halts with the outcome "Invalid".
            #        Else, continue.
            # Find u_min
            u_min = len(route.path)  # Set u_min to N+1, but verifying AS is included which is why we skip +1
            for i, curr_asys in enumerate(route.path):
                if i + 2 < len(
                        route.path):  # Verifying AS contained in route AND make sure we are not at the end already and produce an array out-of-bounds exception
                    next_asys = route.path[i + 1]
                    # print('Curr AS: ', curr_asys.as_id)
                    # print('Curr AS ASPA', curr_asys.aspa)
                    # print('Next AS: ', next_asys.as_id)
                    if curr_asys.aspa != None and not next_asys.as_id in curr_asys.aspa[
                        1]:  # ASPA present but next_asys not contained in provider list
                        u_min = route.path.index(next_asys) + 1  # since index returns position in array starting with 0
                        break

            # Find v_max
            v_max = 0
            for i, curr_asys in enumerate(reversed(route.path)):
                if i == 0:  # skip first AS as it is the verifying AS
                    continue
                if i + 1 < len(
                        route.path):  # Make sure we are not at the end already and produce an array out-of-bounds exception
                    next_asys = list(reversed(route.path))[i + 1]
                    # print('Curr AS: ', curr_asys.as_id)
                    # print('Curr AS ASPA', curr_asys.aspa)
                    # print('Next AS: ', next_asys.as_id)
                    if curr_asys.aspa != None and not next_asys.as_id in curr_asys.aspa[
                        1]:  # ASPA present but next_asys not contained in provider list
                        v_max = route.path.index(next_asys) + 1
                        break

            if u_min <= v_max:
                result = 'Invalid'
                # return result # To avoid overwriting with possibly other results

            if result != 'Invalid':  # To avoid overwriting with possibly other results

                # Step5 - Up-ramp: For 2 ≤ i ≤ N, determine the largest K such that
                #        hop(AS(i-1), AS(i)) = "Provider+" for each i in the range 2 ≤ i ≤
                #        K.  If such a largest K does not exist, then set K = 1.

                # Find largest k
                k = 1
                for i, curr_asys in enumerate(route.path):
                    if i + 2 < len(
                            route.path):  # Verifying AS contained in route AND make sure we are not at the end already and produce an array out-of-bounds exception
                        next_asys = route.path[i + 1]
                        # print('Curr AS: ', curr_asys.as_id)
                        # print('Curr AS ASPA', curr_asys.aspa)
                        # print('Next AS: ', next_asys.as_id)
                        if curr_asys.aspa != None and next_asys.as_id in curr_asys.aspa[
                            1]:  # ASPA present but next_asys not contained in provider list
                            k = route.path.index(next_asys) + 1  # since index returns position in array starting with 0
                        else:
                            break

                # Step6 - Down-ramp: For N-1 ≥ j ≥ 1, determine the smallest L such that
                #        hop(AS(j+1), AS(j)) = "Provider+" for each j in the range N-1 ≥ j
                #        ≥ L.  If such smallest L does not exist, then set L = N.

                # Find smallest L
                l = len(route.path) - 1
                for i, curr_asys in enumerate(reversed(route.path)):
                    if i == 0:  # skip first AS as it is the verifying AS
                        continue
                    if i + 1 < len(
                            route.path):  # Make sure we are not at the end already and produce an array out-of-bounds exception
                        next_asys = list(reversed(route.path))[i + 1]
                        # print('Curr AS: ', curr_asys.as_id)
                        # print('Curr AS ASPA', curr_asys.aspa)
                        # print('Next AS: ', next_asys.as_id)
                        if curr_asys.aspa != None and next_asys.as_id in curr_asys.aspa[
                            1]:  # ASPA present but next_asys not contained in provider list
                            l = route.path.index(next_asys) + 1
                        else:
                            break

                if l - k <= 1:
                    result = 'Valid'
                else:
                    result = 'Unknown'

    else:
        raise Exception("Unknown relationship type", relation)

    # print("Final ASPA validation result is: ", result)
    if False:
        print("Final ASPA validation result is: ", result)
        print("Direction: ", relation)
        print(route)
        for asys in route.path:
            print(asys.aspa)
        print('-----')
        print('')

    return result


def perform_ASCONES_algorithm(route):
    result = False
    # https://datatracker.ietf.org/doc/html/draft-ietf-grow-rpki-as-cones-02
    # We use the ASPA algorithm for validation of ASCones paths! It is much more mature and works very well.
    # The algorithm was adjusted to look at the relationship from the other end, e.g. ASCones view not ASPA view.
    # The result per relationship remains the same, hence the algorithm can be applied, too.

    # Upstream path verification!
    relation = route.final.get_relation(route.first_hop)
    if relation == Relation.CUSTOMER or relation == Relation.PEER:
        # print('')
        # print('-------')
        # print('Relation: ', relation)
        # print('Route: ', route)
        # Step1 - If the AS_PATH has an AS_SET, then the procedure halts with the outcome "Invalid".
        # Step2 - Collapse prepends in the AS_SEQUENCE(s) in the AS_PATH (i.e., keep only the unique AS numbers). Let the resulting ordered sequence be represented by {AS(N), AS(N-1), ..., AS(2), AS(1)}, where AS(1) is the first-added (i.e., origin) AS and AS(N) is the last-added AS and neighbor to the receiving/validating AS.
        # Step3 - If N = 1, then the procedure halts with the outcome "Valid". Else, continue.
        if len(route.path) < 2:  # case never happens
            raise Exception('Route length below verifyable!')
        elif len(
                route.path) == 2:  # the route object also contains the AS that currently validates as destination. We know this must be a customer and don´t need AS-Cones for it.
            result = 'Valid'
        # Step4 - At this step, N ≥ 2. If there is an i such that 2 ≤ i ≤ N and hop(AS(i-1), AS(i)) = "Not Provider+", then the procedure halts with the outcome "Invalid". Else, continue.
        # Step5 - If there is an i such that 2 ≤ i ≤ N and hop(AS(i-1), AS(i)) = "No Attestation", then the procedure halts with the outcome "Unknown". Else, the procedure halts with the outcome "Valid".
        else:
            result = 'Valid'
            for i, curr_asys in enumerate(list(reversed(route.path))):
                if i == 0:  # skip first AS as it is the verifying AS
                    continue

                elif i + 1 < len(route.path):
                    next_asys = list(reversed(route.path))[i + 1]
                    if curr_asys.ascones != None and not next_asys.as_id in curr_asys.ascones[1]:
                        # Invalid
                        result = 'Invalid'
                        break
                    elif curr_asys.ascones == None:  # ASCONES not present
                        # No attestation
                        result = 'Unknown'
                        break
                    else:
                        # ASCONES object present and current AS authorized its upstream
                        pass

    elif relation == Relation.PROVIDER:
        # print('')
        # print('-------')
        # print('Relation: ', relation)
        # print('Route: ', route)
        # Step1 - If the AS_PATH has an AS_SET, then the procedure halts with the outcome "Invalid".
        # Step2 - Collapse prepends in the AS_SEQUENCE(s) in the AS_PATH (i.e., keep only the unique AS numbers). Let the resulting ordered sequence be represented by {AS(N), AS(N-1), ..., AS(2), AS(1)}, where AS(1) is the first-added (i.e., origin) AS and AS(N) is the last-added AS and neighbor to the receiving/validating AS.
        # Step3 - If 1 ≤ N ≤ 2, then the procedure halts with the outcome "Valid". Else, continue.
        if len(route.path) < 2:  # case never happens
            raise Exception('Route length below verifyable!')
        elif len(route.path) == 2 or len(
                route.path) == 3:  # the route object also contains the AS that currently validates as destination
            # Length 2: This case covers an upstream sending a route directly.
            # Length 3: This case covers essentially three scenarios. The upstream of the verifying AS receives the route either from a customer, a peer, or it's upstream. All trivially valid cases.
            result = 'Valid'
        else:  # For paths > 3
            # Step4 - At this step, N ≥ 3.  Given the above-mentioned ordered sequence,
            #        find the lowest value of u (2 ≤ u ≤ N) for which hop(AS(u-1),
            #        AS(u)) = "Not Provider+".  Call it u_min.  If no such u_min
            #        exists, set u_min = N+1.  Find the highest value of v (N-1 ≥ v ≥
            #        1) for which hop(AS(v+1), AS(v)) = "Not Provider+".  Call it
            #        v_max.  If no such v_max exists, then set v_max = 0.  If u_min ≤
            #        v_max, then the procedure halts with the outcome "Invalid".
            #        Else, continue.
            # Find u_min
            u_min = len(route.path)  # Set u_min to N+1, but verifying AS is included which is why we skip +1
            for i, curr_asys in enumerate(route.path):
                if i + 2 < len(
                        route.path):  # Verifying AS contained in route AND make sure we are not at the end already and produce an array out-of-bounds exception
                    next_asys = route.path[i + 1]
                    # print('Curr AS: ', curr_asys.as_id)
                    # print('Next AS: ', next_asys.as_id)
                    # print('Next AS ASCONES', next_asys.ascones)
                    if next_asys.ascones != None and not curr_asys.as_id in next_asys.ascones[
                        1]:  # ASCONES present but curr_asys not contained in customer list
                        u_min = route.path.index(next_asys) + 1  # since index returns position in array starting with 0
                        break

            # Find v_max
            v_max = 0
            for i, curr_asys in enumerate(reversed(route.path)):
                if i == 0:  # skip first AS as it is the verifying AS
                    continue
                if i + 1 < len(
                        route.path):  # Make sure we are not at the end already and produce an array out-of-bounds exception
                    next_asys = list(reversed(route.path))[i + 1]
                    # print('Curr AS: ', curr_asys.as_id)
                    # print('Next AS: ', next_asys.as_id)
                    # print('Next AS ASCONES', next_asys.ascones)
                    if next_asys.ascones != None and not curr_asys.as_id in next_asys.ascones[
                        1]:  # ASCONES present but curr_asys not contained in customer list
                        v_max = route.path.index(next_asys) + 1
                        break

            if u_min <= v_max:
                result = 'Invalid'
                # return result # To avoid overwriting with possibly other results

            if result != 'Invalid':  # To avoid overwriting with possibly other results
                # Step5 - Up-ramp: For 2 ≤ i ≤ N, determine the largest K such that
                #        hop(AS(i-1), AS(i)) = "Provider+" for each i in the range 2 ≤ i ≤
                #        K.  If such a largest K does not exist, then set K = 1.

                # Find largest k
                k = 1
                for i, curr_asys in enumerate(route.path):
                    if i + 2 < len(
                            route.path):  # Verifying AS contained in route AND make sure we are not at the end already and produce an array out-of-bounds exception
                        next_asys = route.path[i + 1]
                        # print('Curr AS: ', curr_asys.as_id)
                        # print('Next AS: ', next_asys.as_id)
                        # print('Next AS ASCONES', next_asys.ascones)
                        if next_asys.ascones != None and curr_asys.as_id in next_asys.ascones[
                            1]:  # ASCONES present but curr_asys not contained in customer list
                            k = route.path.index(next_asys) + 1  # since index returns position in array starting with 0
                        else:
                            break

                # Step6 - Down-ramp: For N-1 ≥ j ≥ 1, determine the smallest L such that
                #        hop(AS(j+1), AS(j)) = "Provider+" for each j in the range N-1 ≥ j
                #        ≥ L.  If such smallest L does not exist, then set L = N.

                # Find smallest L
                l = len(route.path) - 1
                for i, curr_asys in enumerate(reversed(route.path)):
                    if i == 0:  # skip first AS as it is the verifying AS
                        continue
                    if i + 1 < len(
                            route.path):  # Make sure we are not at the end already and produce an array out-of-bounds exception
                        next_asys = list(reversed(route.path))[i + 1]
                        # print('Curr AS: ', curr_asys.as_id)
                        # print('Next AS: ', next_asys.as_id)
                        # print('Next AS ASCONES', next_asys.ascones)
                        if next_asys.ascones != None and curr_asys.as_id in next_asys.ascones[
                            1]:  # ASCONES present but curr_asys not contained in customer list
                            l = route.path.index(next_asys) + 1
                        else:
                            break

                if l - k <= 1:
                    result = 'Valid'
                else:
                    result = 'Unknown'

    else:
        raise Exception("Unknown relationship type", relation)

    return result


class ASPAPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'ASPAPolicy'

    def __str__(self):
        return self.name

    # https://datatracker.ietf.org/doc/html/draft-ietf-sidrops-aspa-verification-16
    def accept_route(self, route: Route) -> bool:
        result = perform_ASPA_algorithm(route)

        # Accepts the route if none of the elements with ASPA activated has returned INVALID
        return super().accept_route(route) and not (result == 'Invalid')


class ASCONESPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'ASCONESPolicy'

    def __str__(self):
        return self.name

    # https://datatracker.ietf.org/doc/html/draft-ietf-sidrops-aspa-verification-16
    def accept_route(self, route: Route) -> bool:
        result = perform_ASCONES_algorithm(route)

        # Accepts the route if none of the elements with ASPA activated has returned INVALID
        return super().accept_route(route) and not (result == 'Invalid')


def perform_down_only(route) -> bool:
    do_set = route.local_data_part_do != ""
    remote_as = route.path[len(route.path) - 2]
    relation_to_sender = remote_as.get_relation(route.final)

    # Ingress policy 1:
    # If a route with DO Community is received from a Customer or RS-client,
    # then it is a route leak and MUST be dropped. The procedure halts.
    if do_set and (relation_to_sender == Relation.CUSTOMER or relation_to_sender == Relation.RS_CLIENT):
        #print("Down Only validation detected Route Leak. Dropping Route.")
        return False

    # Ingress policy 2:
    # If a route with DO Community is received from a Peer (non-transit) and
    # at least one DO value is not equal to the sending neighbor's ASN, then
    # it is a route leak and MUST be dropped. The procedure halts.
    if do_set and relation_to_sender == Relation.PEER:
        #print("[Relation]: CUSTOMER; [Down_Only]: True ;[Atr]: ", route.local_data_part_do, "; [Length]: ",
        #      len(route.local_data_part_do), "; [PreviousASN]: ", route.final.as_id)
        for i in route.local_data_part_do.split():
            if i != route.first_hop.as_id:
                #print("Reason 2")
                return False

    # Ingress policy 3:
    # If a route is received from a Provider, Peer, or RS, then a DO
    # Community MUST be added with a value equal to the sending neighbor's ASN.
    if relation_to_sender == Relation.PROVIDER or relation_to_sender == Relation.PEER or relation_to_sender == Relation.RS_CLIENT:
        route.local_data_part_do += str(remote_as.as_id) + " "
    return True


# RFC 9234
def perform_only_to_customer(route) -> bool:
    do_set = route.local_data_part_do != ""
    remote_as = route.path[len(route.path) - 2]
    relation_to_sender = remote_as.get_relation(route.final)

    # Ingress policy 1:
    # If a route with the OTC Attribute is received from a Customer or an RS-Client, then it is a route
    # leak and be considered ineligible.
    if do_set and (relation_to_sender == Relation.CUSTOMER or relation_to_sender == Relation.RS_CLIENT):
        # print("Down Only validation detected Route Leak. Dropping Route.")
        return False

    # Ingress policy 2:
    # If a route with the OTC Attribute is received from a Peer (i.e., remote AS with a Peer Role) and
    # the Attribute has a value that is not equal to the remote (i.e., Peer's) AS number, then it is a
    # route leak and be considered ineligible
    if do_set and relation_to_sender == Relation.PEER:
        for i in route.local_data_part_do.split():
            if i != remote_as.as_id:
                return False

    # Ingress policy 3:
    # If a route is received from a Provider, a Peer, or an RS and the OTC Attribute is not present,
    # then it be added with a value equal to the AS number of the remote AS.
    if not do_set and (relation_to_sender == Relation.PROVIDER or relation_to_sender == Relation.PEER or
                       relation_to_sender == Relation.ROUTE_SERVER):
        route.local_data_part_do += str(remote_as.as_id) + " "

    return True


class OnlyToCustomerPolicy(DefaultPolicy):
    def __init__(self):
        self.name = 'OnlyToCustomerPolicy'

    def __str__(self):
        return self.name

    def accept_route(self, route: Route) -> bool:
        super_result = DefaultPolicy().accept_route(route)
        result = perform_only_to_customer(route)
        result_alt = perform_down_only(route)
        if result != result_alt:
            print("IMPLEMENTATION ERROR!")
        return result if super_result else False

    def forward_to(self, route: Route, relation: Relation) -> bool:
        do_set = route.local_data_part_do != ""
        super_forward = DefaultPolicy().forward_to(route, relation)
        asn = route.final

        if super_forward:
            # egress policy 1
            # If a route is to be advertised to a Customer, a Peer, or an RS-Client (when the
            # sender is an RS), and the OTC Attribute is not present, then when advertising the
            # route, an OTC Attribute MUST be added with a value equal to the AS number of the
            # local AS.
            if not do_set and (relation == Relation.CUSTOMER or relation == Relation.PEER or
                               relation == Relation.RS_CLIENT):
                route.local_data_part_do += asn.as_id

            # egress policy 2
            # If a route already contains the OTC Attribute, it MUST NOT be propagated to Providers, Peers,
            # or RSes.
            if do_set and (
                    relation == Relation.PROVIDER or relation == Relation.PEER or relation == Relation.ROUTE_SERVER):
                return False

        return super_forward
