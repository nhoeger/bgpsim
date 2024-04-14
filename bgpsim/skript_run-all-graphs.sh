#!/bin/bash
# More trials provide more precise results, but increase running time linearly
number_of_trials=10

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ... [100,0,100] ... [0,100,100] ... [100,100,100]
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_one_down_only caida-data/20221101.as-rel.txt outputs/figure_one_down_only_"$number_of_trials"trials | tee down_only_one"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_one_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_one_only_to_customer_"$number_of_trials"trials | tee otc_one"$number_of_trials".txt

# Random Deployment for Down Only and Only To Customer
# [0,0,0] ... [100,0,0] ... [0,100,0]
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_two_down_only caida-data/20221101.as-rel.txt outputs/figure_two_down_only_"$number_of_trials"trials | tee down_only_two"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_two_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_two_only_to_customer_"$number_of_trials"trials | tee otc_two"$number_of_trials".txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0]
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_three_down_only caida-data/20221101.as-rel.txt outputs/figure_three_down_only_"$number_of_trials"trials | tee down_only_three"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_three_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_three_only_to_customer_"$number_of_trials"trials | tee otc_three"$number_of_trials".txt

# Top ISP Deployment
# [0,0,0] ... [100,0,0] ... [0,100,0] ... [100,100,0] ... [0,0,100] ...
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_four_down_only caida-data/20221101.as-rel.txt outputs/figure_four_down_only_"$number_of_trials"trials | tee down_only_four"$number_of_trials".txt
pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_four_only_to_customer caida-data/20221101.as-rel.txt outputs/figure_four_only_to_customer_"$number_of_trials"trials | tee otc_four"$number_of_trials".txt

# Combined approach of ASPA and Down Only
# Both random and top ISP
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_combined_random caida-data/20221101.as-rel.txt outputs/figure_combined_random_"$number_of_trials"trials | tee combined_random_"$number_of_trials".txt
#pipenv run python -m bgpsecsim generate --trials "$number_of_trials" figure_combined_isp caida-data/20221101.as-rel.txt outputs/figure_combined_isp"$number_of_trials"trials | tee combined_isp"$number_of_trials".txt



