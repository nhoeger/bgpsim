#!/bin/bash
for ((i=1; i<=10000; i *= 10)); do
  pipenv run python -m bgpsecsim generate --trials "$i" deviation_figure caida-data/20221101.as-rel.txt outputs/figure_one_down_only_100trials | tee deviation.txt
done
