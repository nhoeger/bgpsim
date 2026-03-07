#!/bin/bash
# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ... [100,0,100] ... [0,100,100] ... [100,100,100]
python -m bgpsecsim generate --trials 1 test_customer_cone caida-data/20250601.as-rel.txt outputs/figure_one_down_only_100trials
python -m bgpsecsim generate --trials 1 test_customer_cone caida-data/20250601.as-rel.txt outputs/figure_one_only_to_customer_100trials

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0]
python -m bgpsecsim generate --trials 1 figure_two_down_only caida-data/20250601.as-rel.txt outputs/figure_two_down_only_250trials
python -m bgpsecsim generate --trials 1 figure_two_only_to_customer caida-data/20250601.as-rel.txt outputs/figure_two_only_to_customer_250trials

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0]
python -m bgpsecsim generate --trials 1 figure_three_down_only caida-data/20250601.as-rel.txt outputs/figure_three_down_only_250trials
python -m bgpsecsim generate --trials 1 figure_three_only_to_customer caida-data/20250601.as-rel.txt outputs/figure_three_only_to_customer_250trials

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ...
python -m bgpsecsim generate --trials 1 figure_four_down_only caida-data/20250601.as-rel.txt outputs/figure_four_down_only_250trials
python -m bgpsecsim generate --trials 1 figure_four_only_to_customer caida-data/20250601.as-rel.txt outputs/figure_four_only_to_customer_250trials