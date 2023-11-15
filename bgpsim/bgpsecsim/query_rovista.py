import json
import os
import pickle
import sys
from datetime import timedelta
from multiprocessing import Pool
import time

import dateutil.parser
import requests

def query(as_id):
    headers = {'Accept': 'application/json'}
    result = requests.get('https://api.rovista.netsecurelab.org/rovista/api/AS-rov-scores/'+str(as_id), headers=headers)

    if result == []:
        pass
    else:
        print('Writing JSON for AS: ', as_id)
        try:
            with open(filename + str(as_id) + ".json", "w") as outfile:
                json.dump(result.json(), outfile)

        except Exception as e:
            print(as_id, e)

    time.sleep(1)


def query_rovista(filename, PROCESSES):
    as_ids = []
    for i in range(401308):  # max number of as_ids
        as_ids.append(i)

    # create and configure the process pool
    with Pool(PROCESSES) as pool:
        # issues tasks to process pool
        for result in pool.map(query, as_ids):
            pass
    print('Finished execution')


def build_resultset(filename):
    files = os.listdir(filename)

    start = '2011-01-21'
    end = '2023-10-07'

    start_date = dateutil.parser.parse(start).date()
    end_date = dateutil.parser.parse(end).date()

    delta = end_date - start_date  # returns timedelta

    days = {}
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        days[day.isoformat()] = []

    i = 0
    for file in files:
        i += 1
        print(i)
        with open(filename + file) as f:
            data = json.load(f)
            if data == []:
                continue
            else:
                for element in data:
                    if element['ratio'] == 1.0:
                        days[element['recordDate']].append(element['asn'])

    with open(filename + 'rov_results.pickle', 'wb') as f:
        pickle.dump(days, f)


def read_resultset(filename):
    with open(filename + 'rov_results.pickle', 'rb') as f:
        data = pickle.load(f)
    #for day in data:
    #    print(data[day])
    #    print('---')

    print(len(data))

if __name__ == '__main__':
    PROCESSES = 10
    filename = '/opt/simulation/rovista/'

    #query_rovista(filename, PROCESSES)

    #build_resultset(filename)

    read_resultset(filename)




