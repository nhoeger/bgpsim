#!/bin/bash
# Run Down Only first
pipenv run python -m bgpsecsim generate --trials 100 figure_one_down_only caida-data/20221101.as-rel.txt outputs/figure_down_only_1_100trials | tee down_only_one.txt
pipenv run python -m bgpsecsim generate --trials 100 figure_one_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_down_only_1_100trials | tee otc_one.txt




