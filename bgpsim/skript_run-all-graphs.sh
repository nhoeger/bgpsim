#!/bin/bash
# More trials provide more precise results, but increase running time linearly

## !!! Low number only for testing
number_of_trials=1

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ... [100,0,100] ... [0,100,100] ... [100,100,100]
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_1 caida-data/20240501.as-rel.txt outputs/figure_roles_1_"$number_of_trials"trials | tee figure_roles_1_"$number_of_trials".txt

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0]
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_2 caida-data/20240501.as-rel.txt outputs/figure_roles_2_"$number_of_trials"trials | tee figure_roles_2_"$number_of_trials".txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0]
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_3 caida-data/20240501.as-rel.txt outputs/figure_roles_3_"$number_of_trials"trials | tee figure_roles_3_"$number_of_trials".txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ...
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_4 caida-data/20240501.as-rel.txt outputs/figure_roles_4_"$number_of_trials"trials | tee figure_roles_4_"$number_of_trials".txt

# Combined approach of ASPA and Down Only
# Both random and top ISP


## !!! Low number only for testing
number_of_trials=1
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_5 caida-data/20240501.as-rel.txt outputs/figure_roles_5_"$number_of_trials"trials | tee figure_roles_5_"$number_of_trials".txt


