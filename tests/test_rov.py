import unittest
import os
import csv
import re

import bgpsecsim.as_graph as as_graph
from bgpsecsim.as_graph import ASGraph
from bgpsecsim.routing_policy import (
    RPKIPolicy, DefaultPolicy
)

AS_REL_FILEPATH = os.path.join(os.path.dirname(__file__), '../caida-data', '20250601.as-rel.txt')

class TestROVGraph(unittest.TestCase):
    def test_rovista_graph(self):
        # Create AS graph based on CAIDA AS relationship data
        graph = ASGraph(as_graph.parse_as_rel_file(AS_REL_FILEPATH))

        # Load rovista scores from caida-data/asn_rov_scores.csv into a dictionary
        rovista_scores = {}
        with open(os.path.join(os.path.dirname(__file__), '../caida-data', 'asn_rov_scores_cleaned.csv'), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                asn = row.get('ASN')
                score = row.get('rovista_score')
                if asn is None or score is None:
                    continue
                # Remove any "AS" prefix and convert to int
                asn = re.sub(r'^(?:as|s)', '', asn.strip(), flags=re.IGNORECASE)
                if not asn.isdigit():
                    continue
                rovista_scores[int(asn)] = float(score)

        print(f"Loaded {len(rovista_scores)} ROV scores")

        # Asign RPKI policies based on ROVista scores
        for as_id, score in rovista_scores.items():
            asys = graph.get_asys(str(as_id))
            if asys is not None and score == 1.0:
                asys.policy = RPKIPolicy()
                

        # Now check: All ASes with ROVista score == 1.0 should have RPKIPolicy, others DefaultPolicy
        for as_id, score in rovista_scores.items():
            asys = graph.get_asys(str(as_id))
            if asys is not None:
                if score == 1.0:
                    self.assertIsInstance(asys.policy, RPKIPolicy, f"AS{as_id} should have RPKIPolicy")
                else:
                    self.assertIsInstance(asys.policy, DefaultPolicy, f"AS{as_id} should have DefaultPolicy")

        # Randomly selected target AS to check the find_routes_to method
        target_as_id = '7' 
        target_asys = graph.get_asys(target_as_id)
        if target_asys is not None:
            graph.find_routes_to(target_asys)
            
        # Check a random host AS (e.g., AS9) to see if it has a route to the target AS
        host_as_id = '9'
        host_asys = graph.get_asys(host_as_id)
        if host_asys is not None and target_asys is not None:
            print(f"Routing Table for AS{host_as_id}: {host_asys.routing_table}")
        


if __name__ == '__main__':
    unittest.main()