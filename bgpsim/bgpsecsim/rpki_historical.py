import json
import math
import multiprocessing
import sys
from datetime import date,datetime, timedelta
from random import random
from time import sleep
import dateutil.parser
from multiprocessing import Pool
import numpy as np
import tarfile
import base64
import dump_json
from asn1crypto.cms import ContentInfo
from asn1crypto.crl import CertificateList
import pickle

# Calculation of RPKI development:
# https://stats.labs.apnic.net/roa/XA
# Objects:
# 1.7.2012 - 0\% (calculated backwards)
# 1.1.2014 - 3.77\%
# 1.1.2020 - 19.1\%
# 1.1.2023 - 38.46\%
# Two linear movements:
# 2190 days, 0,007\% increase per day
# 1095 days, 0.01768\% increase per day

# https://rovista.netsecurelab.org/analytics
# Policy:
# 18.9.2019 - 0\% (calculated backwards)
# 2.1.2022 - 6.633\%
# 7.1.2023 - 9.15\%
# 1.6.2023 - 10.71\%
# 2.1.22 - 1.6.23 are 515 days. Therefore, 10.71 - 6.633 = 4,077
# 4,077 / 515 = growth rate of 0,0079

# def cumulative_roa_percentage(day):
#     first_r = 0.007  # Daily growth rate for the first interval
#     second_r = 0.01768  # Daily growth rate for the second interval
#     second_period = 2750
#
#     if day <= second_period:  # From July 1, 2012, to January 1, 2020
#         # Calculate the cumulative percentage of ROAs created up to the given day
#         cumulative_percentage = day * first_r
#     else:  # After January 1, 2020
#         # Calculate the cumulative percentage of ROAs created up to the given day
#         cumulative_percentage = (day - second_period) * second_r + second_period * first_r
#
#     return cumulative_percentage
#
# def cumulative_rpki_percentage(day):
#     cumulative_roa_value = cumulative_roa_percentage(day)
#     print(f"Up to day {day}, the cumulative percentage of ROAs created is approximately {cumulative_roa_value:.2f}%")
#
#     if day < 2635:  # number of days between 1.7.2012 and 18.09.2019 (when ROV deployment started)
#         cumulative_rov_percentage = 0
#     else:
#         adjusted_day = day - 2635
#         cumulative_rov_percentage = 0.0079 * adjusted_day
#     print(f"Up to day {day}, the cumulative percentage of ROV is approximately {cumulative_rov_percentage:.2f}%")
#     return cumulative_roa_value, cumulative_rov_percentage
#
# f_date = date(2012, 7, 1) #Leave beginning as is!
# l_date = date(2023, 6, 1)
# delta = l_date - f_date
#
# rpki_history = np.zeros((delta.days, 2))
# cumulative_roa_value = np.zeros(delta.days)
# cumulative_rov_percentage = np.zeros(delta.days)
#
# for i in range(delta.days):
#     cumulative_roa_value[i], cumulative_rov_percentage[i] = cumulative_rpki_percentage(i)


#np.save('/opt/simulation/bgpsim/outputs/rpki_history.npy', rpki_history) #Save numpy array for later use



# Code extended from Ziggy@ NLnet Labs!
# https://github.com/NLnetLabs/ziggy/blob/master/ziggy.py
def get_asns(day):
    date = dateutil.parser.parse(day).date()
    #test = "/opt/simulation/bgpsim/test/repo.tar.gz"
    #day_tarfiles.append(test)

    base_path = "/opt/simulation/rpki_history"
    tals = ["afrinic.tal", "apnic-afrinic.tal", "apnic-arin.tal", "apnic-iana.tal", "apnic-lacnic.tal", "apnic-ripe.tal", "apnic.tal", "arin.tal", "lacnic.tal", "ripencc.tal"]

    day_tarfiles = []
    for tal in tals:
        tal_file = '{}/{}/{:04d}/{:02d}/{:02d}/repo.tar.gz'.format(base_path, tal, date.year, date.month, date.day)
        day_tarfiles.append(tal_file)

    print(day_tarfiles)

    asns = set()
    for tarchive in day_tarfiles:
        sys.stdout.write('Processing {} ... '.format(tarchive))
        sys.stdout.flush()

        try:
            t = tarfile.open(tarchive)


            for member in t.getmembers():
                if member.name.endswith('.roa') and member.isfile():
                    der_byte_string = t.extractfile(member.name).read()
                    ext_class = ContentInfo
                    
                    # This is code is extended from Job Snijders
                    # Parse ASN.1 data
                    try:
                        parsed = ext_class.load(der_byte_string)
                    except Exception as e:
                        print('Could not parse file: ', e)

                    try:
                        data = parsed.native

                        if type(parsed) is ContentInfo:
                             if data['content']['encap_content_info']['content_type'] == 'routeOriginAuthz':
                                dump_json.process_roa(data['content']['encap_content_info']['content'])

                        asns.add(data['content']['encap_content_info']['content']['asID'])

                    except Exception as e:
                        print(e)
        except Exception as e:
            print(e)


    return [day, asns]


# protect the entry point
def start_processing(start, end, filename, PROCESSES):
    start_date = dateutil.parser.parse(start).date()
    end_date = dateutil.parser.parse(end).date()

    delta = end_date - start_date  # returns timedelta

    days = {}
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        days[day.isoformat()] = 0

    # create and configure the process pool
    with Pool(PROCESSES) as pool:
        # issues tasks to process pool
        for result in pool.map(get_asns, days.keys()):
            days[result[0]] = result[1]

    with open(filename, 'wb') as f:
        pickle.dump(days, f)

def start_reading(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    for day in data:
        print(data[day])
        print('---')


if __name__ == '__main__':

    PROCESSES = 100
    start = '2011-01-21'
    #end = '2023-10-07'
    end = '2011-01-22'
    filename = '/opt/simulation/rpki_roa_history.pickle'
    #Change path in Worker threat, too!

    #start_processing(start, end, filename, PROCESSES)
    #start_reading(filename)





