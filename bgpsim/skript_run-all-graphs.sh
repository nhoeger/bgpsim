#!/bin/bash

# More trials and steps provide more precise results, but increase running time
number_of_trials=1
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" otc_figures caida-data/20240501.as-rel.txt outputs/figure_roles_1_"$number_of_trials"trials | tee figure_roles_1_"$number_of_trials".txt
