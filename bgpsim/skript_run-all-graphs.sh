#!/bin/bash
# Random Deployment for Down Only and Only To Customer
# pipenv run python -m bgpsecsim generate --trials 100 figure_one_down_only caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one.txt
# pipenv run python -m bgpsecsim generate --trials 100 figure_one_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_one_only_to_customer_100trials | tee otc_one.txt

# Top ISPs Deployment for Down Only and Only To Customer
pipenv run python -m bgpsecsim generate --trials 250 figure_two_down_only caida-data/20221101.as-rel.txt outputs/figure_two_down_only_250trials | tee down_only_two250.txt
pipenv run python -m bgpsecsim generate --trials 250 figure_two_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_two_only_to_customer_250trials | tee otc_two250.txt





