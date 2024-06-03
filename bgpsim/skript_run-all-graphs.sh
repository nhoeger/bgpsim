#!/bin/bash
# More trials provide more precise results, but increase running time linearly
number_of_trials=100

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ... [100,0,100] ... [0,100,100] ... [100,100,100]
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_one_down_only caida-data/20240501.as-rel.txt outputs/figure_one_down_only_"$number_of_trials"trials | tee down_only_one"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_one_only_to_customer caida-data/20240501.as-rel.txt outputs/figure_one_only_to_customer_"$number_of_trials"trials | tee otc_one"$number_of_trials".txt

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0]
##pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_two caida-data/20240501.as-rel.txt outputs/figure_two_"$number_of_trials"trials | tee figure_two_"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_two_only_to_customer caida-data/20240501.as-rel.txt outputs/figure_two_only_to_customer_"$number_of_trials"trials | tee otc_two"$number_of_trials".txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0]
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_3 caida-data/20240501.as-rel.txt outputs/figure_roles_3_"$number_of_trials"trials | tee figure_roles_3_"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_three_only_to_customer caida-data/20240501.as-rel.txt outputs/figure_three_only_to_customer_"$number_of_trials"trials | tee otc_three"$number_of_trials".txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ...
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_4 caida-data/20240501.as-rel.txt outputs/figure_roles_4_"$number_of_trials"trials | tee figure_roles_4_"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_four_only_to_customer caida-data/20240501.as-rel.txt outputs/figure_four_only_to_customer_"$number_of_trials"trials | tee otc_four"$number_of_trials".txt

# Combined approach of ASPA and Down Only
# Both random and top ISP
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_roles_5 caida-data/20240501.as-rel.txt outputs/figure_roles_5_"$number_of_trials"trials | tee figure_roles_5_"$number_of_trials".txt

# Hopefully no longer needed:
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_combined_isp caida-data/20240501.as-rel.txt outputs/figure_combined_isp"$number_of_trials"trials | tee combined_isp"$number_of_trials".txt



