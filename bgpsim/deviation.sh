#!/bin/bash
#for ((i=1; i<=2; i++)); do
#  pipenv run python -m bgpsecsim generate --trials 1 deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
#done
pipenv run python -m bgpsecsim generate --trials 1 deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
pipenv run python -m bgpsecsim generate --trials 10 deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
pipenv run python -m bgpsecsim generate --trials 100 deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
pipenv run python -m bgpsecsim generate --trials 1000 deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
pipenv run python -m bgpsecsim generate --trials 10000 deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee down_only_one250.txt
