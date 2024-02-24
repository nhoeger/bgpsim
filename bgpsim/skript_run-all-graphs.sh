#!/bin/bash
# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ... [100,0,100] ... [0,100,100] ... [100,100,100]
pipenv run python -m bgpsecsim generate --trials 250 figure_one_down_only caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
pipenv run python -m bgpsecsim generate --trials 250 figure_one_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_one_only_to_customer_100trials | tee otc_one250.txt

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0]
pipenv run python -m bgpsecsim generate --trials 250 figure_two_down_only caida-data/20221101.as-rel.txt outputs/figure_two_down_only_250trials | tee down_only_two250.txt
pipenv run python -m bgpsecsim generate --trials 100 figure_two_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_two_only_to_customer_250trials | tee otc_two250.txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0]
pipenv run python -m bgpsecsim generate --trials 250 figure_three_down_only caida-data/20221101.as-rel.txt outputs/figure_three_down_only_250trials | tee down_only_three250.txt
pipenv run python -m bgpsecsim generate --trials 250 figure_three_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_three_only_to_customer_250trials | tee otc_three250.txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ...
pipenv run python -m bgpsecsim generate --trials 250 figure_four_down_only caida-data/20221101.as-rel.txt outputs/figure_four_down_only_250trials | tee down_only_four250.txt
pipenv run python -m bgpsecsim generate --trials 250 figure_four_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_four_only_to_customer_250trials | tee otc_four250.txt



