import sys
from fractions import Fraction
import itertools
import math
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import random
import statistics
from typing import List, Sequence, Tuple
import matplotlib
from numpy import asarray
from numpy import savetxt
import pickle as pkl
from timeit import default_timer as timer
from datetime import date,datetime, timedelta

def figure11(filename):
    indices = np.arange(0, 101, 1)

    data = np.load(filename + '.npy')  # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5,4))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=data[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(12)

    plt.rc('font', size=12)  # controls default text sizes

    plt.xticks([0,20,40,60,80,100],['0', '15', '30', '45', '60', '74.1'])
    plt.yticks([0,20,40,60,80,100],['0', '15', '30', '45', '60', '74.1'])
    ax.yaxis.labelpad = -1 #margin of x-label
    ax.xaxis.labelpad = 4 #margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment [# ASes in k]")

    #plt.plot(get_rpki_history()[1], get_rpki_history()[0], linestyle='--', color='black')
    rpki_start_date = date(2012, 7, 1) #ROA start date
    #rpki_start_date = date(2019, 9, 18) #ROV start date
    a = ax.plot(get_rpki_history(rpki_start_date)[1][:], get_rpki_history(rpki_start_date)[0][:], linestyle='solid', color='cyan', label='RPKI projection', linewidth=3)
    #b = ax.plot(get_rpki_history(rpki_start_date)[1][2550:], get_rpki_history(rpki_start_date)[0][2550:]-18.5, linestyle='--', color='blue', label='Accelerated RPKI projection')
    plt.ylim(-5, 105)

    #leg = ax.legend([a,b], ['Original RPKI projection', 'Accelerated RPKI projection'], loc="lower right")
    leg = ax.legend(loc="lower right")
    #leg.legendHandles[0].set_color('black')
    #leg.legendHandles[1].set_color('blue')

    # Get the bounding box of the original legend
    bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())

    # Change to location of the legend.
    xOffset = -0.02
    yOffset = 0.05
    bb.x0 += xOffset
    bb.x1 += xOffset
    bb.y0 += yOffset
    bb.y1 += yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    #plt.show()

    plt.savefig(filename + '.svg', format="svg")

def figure13(filename):
    data = np.load(filename + '.npy')  # Load numpy array

    #Means:
    # 10 trials:  1.1693734296415377
    # 100 trials  1.092673738205532 (seed 8 would be a match)
    # 1000 trials 1.1084077289252254 (seed 1 would be a match)
    #Deviations:
    # 10 trials:  1.573052444997361
    # 100 trials  0.4562148887745692
    # 1000 trials 0.15553963175077437

    ten_trials_mean = np.mean(data[0])
    hundred_trials_mean = np.mean(data[1])
    thousand_trials_mean = np.mean(data[2])
    tenthousand_trials_mean = np.mean(data[3])

    ten_trials_std = np.std(data[0])
    hundred_trials_std = np.std(data[1])
    thousand_trials_std = np.std(data[2])
    tenthousand_trials_std = np.std(data[3])

    print('Means: ', ten_trials_mean, hundred_trials_mean, thousand_trials_mean, tenthousand_trials_mean)
    print('Deviations: ', ten_trials_std, hundred_trials_std, thousand_trials_std, tenthousand_trials_std)

    # Creating plot
    data = [data[0], data[1], data[2], data[3]]
    fig, ax = plt.subplots(figsize=(8,5))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    # Creating axes instance
    meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='pink', markersize='12')
    bp = ax.boxplot(data, patch_artist=True, notch='True', vert=1, widths=0.7, showmeans=True, meanprops=meanpointprops)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(18)

    colors = ['#44AA99', '#88CCEE','#DDCC77', '#d796ff']

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#8B008B',
                    linewidth=1.5,
                    linestyle=":")

    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color='#8B008B',
                linewidth=2)

    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color='red',
                   linewidth=5)

    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker='D',
                  color='#e7298a',
                  alpha=0.5)

    # Adding title
    #ax.set_title("Mean and standard deviation \n for different number of trials")
    ax.set_ylabel('Route leak success rate [%]')
    plt.xlabel("Number of trials [#]")

    # Removing top axes and right axes
    # ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

    plt.xticks([1,2,3,4],['10', '100', '1.000', '10.000'])
    plt.yticks([0,0.4,0.8,1.2,1.6])

    fig.subplots_adjust(hspace=0.1)
    plt.ylim(0, 1.6)

    # show plot
    #plt.show()

    plt.savefig(filename + '.svg', format="svg")


# ASPA Selection Strategy: top-to-bottom object creation, top-to-bottom policy assignment
# Since we only get interesting findings in the 20x20 lower left of Figure12, we zoom in and make deployment more fine-grained.
def figure15(filename):
    indices = np.arange(0, 101, 1) #Needed for indexing

    data = np.load(filename + '.npy')  # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0, vmax=1)

    fig, ax = plt.subplots(figsize=(5,4))
    for i in range(101):
        plt.scatter(indices, [i] * 101, c=data[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(9)

    plt.rc('font', size=9)  # controls default text sizes
    plt.xticks([0,10,20,30,40,50,60,70,80,90,100],['0','1.5','3','4.5','6','7.5','9','10.5','12','13.5','15'])
    plt.yticks([0,10,20,30,40,50,60,70,80,90,100],['0','1.5','3','4.5','6','7.5','9','10.5','12','13.5','15'])
    ax.yaxis.labelpad = -1 #margin of x-label
    ax.xaxis.labelpad = 4 #margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in thousands]")
    plt.ylabel("Object deployment [# ASes in thousands]")

    #plt.show()

    plt.savefig(filename + '.svg', format="svg")

# ASPA Selection Strategy: top-to-bottom object creation, top-to-bottom policy assignment
# Since we only get interesting findings in the 30x30 lower left of Figure12, we zoom in and make deployment more fine-grained.
def figure16(filename):
    indices = np.arange(0, 101, 1) #Needed for indexing

    data = np.load(filename + '.npy')  # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5,4))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=data[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(12)

    plt.rc('font', size=12)  # controls default text sizes

    plt.xticks([0,20,40,60,80,100],['0','4.4','8.8','13.3','17.7','22.2'])
    plt.yticks([0,20,40,60,80,100],['0','4.4','8.8','13.3','17.7','22.2'])
    ax.yaxis.labelpad = -1 #margin of x-label
    ax.xaxis.labelpad = 4 #margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment [# ASes in k]")

    #plt.show()
    plt.savefig(filename + '.svg', format="svg")


# ASPA Selection Strategy: bottom-to-top object creation, top-to-bottom policy assignment
# Since we only get interesting findings in the 5x100 upper part of Figure14, we zoom in and make deployment more fine-grained.
def figure17(filename):
    indices = np.arange(0, 101, 1) #Needed for indexing

    data = np.load(filename + '.npy')  # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5,4))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=data[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(12)

    plt.rc('font', size=12)  # controls default text sizes
    plt.xticks([0,20,40,60,80,100],['0', '15', '30', '45', '60', '74.1'])
    plt.yticks([0,20,40,60,80,100],['70.4','71.1','71.8','72.6','73.3','74.1'])
    ax.yaxis.labelpad = -1 #margin of x-label
    ax.xaxis.labelpad = 4 #margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment [# ASes in k]")

    #plt.show()
    plt.savefig(filename + '.svg', format="svg")


def figure30(filename):
    indices = np.arange(0, 101, 1)

    data = np.load(filename + '.npy')  # Load numpy array

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green", "yellow", "red"])
    norm = matplotlib.colors.Normalize(vmin=0)

    fig, ax = plt.subplots(figsize=(5.2,1.9))
    #fig.tight_layout(pad=2)

    #ax.margins(x=2)
    #plt.subplots_adjust(top=)
    plt.subplots_adjust(bottom=0.2)

    for i in range(101):
        plt.scatter(indices, [i] * 101, c=data[i], s=[1.0] * 101, alpha=1, cmap=cmap, norm=norm)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(9)

    plt.rc('font', size=9)  # controls default text sizes

    plt.xticks([0,20,40,60,80,100],['0', '15', '30', '45', '60', '74.1'])
    plt.yticks([0,20,40,60,80,100],['0', '2.2', '4.5', '6.8', '9.0', '11.3'])
    ax.yaxis.labelpad = -1 #margin of x-label
    ax.xaxis.labelpad = 1 #margin of x-label

    plt.colorbar();  # show color scale
    plt.xlabel("Policy deployment [# ASes in k]")
    plt.ylabel("Object deployment \n [# ASes in k]")

    #plt.plot(get_rpki_history()[1], get_rpki_history()[0], linestyle='--', color='black')
    rpki_start_date = date(2012, 7, 1) #ROA start date
    #rpki_start_date = date(2019, 9, 18) #ROV start date
    #a = ax.plot(get_rpki_history(rpki_start_date)[1][:], get_rpki_history(rpki_start_date)[0][:], linestyle='--', color='cyan', label='RPKI projection')
    #b = ax.plot(get_rpki_history(rpki_start_date)[1][2550:], get_rpki_history(rpki_start_date)[0][2550:]-18.5, linestyle='--', color='blue', label='Accelerated RPKI projection')
    plt.ylim(-5, 105)

    #leg = ax.legend([a,b], ['Original RPKI projection', 'Accelerated RPKI projection'], loc="lower right")
    #leg = ax.legend(loc="lower right")
    #leg.legendHandles[0].set_color('black')
    #leg.legendHandles[1].set_color('blue')

    # Get the bounding box of the original legend
    #bb = leg.get_bbox_to_anchor().transformed(ax.transAxes.inverted())

    # Change to location of the legend.
    # xOffset = -0.02
    # yOffset = 0.05
    # bb.x0 += xOffset
    # bb.x1 += xOffset
    # bb.y0 += yOffset
    # bb.y1 += yOffset
    # leg.set_bbox_to_anchor(bb, transform=ax.transAxes)

    #plt.show()

    plt.savefig(filename + '.svg', format="svg")

def figure41(filename):
    data = np.load(filename + '.npy')  # Load numpy array

    # Means:
    # 10 trials:  1.1693734296415377
    # 100 trials  1.092673738205532 (seed 8 would be a match)
    # 1000 trials 1.1084077289252254 (seed 1 would be a match)
    # Deviations:
    # 10 trials:  1.573052444997361
    # 100 trials  0.4562148887745692
    # 1000 trials 0.15553963175077437

    ten_trials_mean = np.mean(data[0])
    hundred_trials_mean = np.mean(data[1])
    thousand_trials_mean = np.mean(data[2])
    tenthousand_trials_mean = np.mean(data[3])

    ten_trials_std = np.std(data[0])
    hundred_trials_std = np.std(data[1])
    thousand_trials_std = np.std(data[2])
    tenthousand_trials_std = np.std(data[3])

    print('Means: ', ten_trials_mean, hundred_trials_mean, thousand_trials_mean, tenthousand_trials_mean)
    print('Deviations: ', ten_trials_std, hundred_trials_std, thousand_trials_std, tenthousand_trials_std)

    # Creating plot
    data = [data[0], data[1], data[2], data[3]]
    fig, ax = plt.subplots(figsize=(8, 5))
    plt.subplots_adjust(bottom=0.2, left=0.2)

    # Creating axes instance
    meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='pink', markersize='12')
    bp = ax.boxplot(data, patch_artist=True, notch='True', vert=1, widths=0.7, showmeans=True, meanprops=meanpointprops)

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                 ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(18)

    colors = ['#44AA99', '#88CCEE', '#DDCC77', '#d796ff']

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    # changing color and linewidth of
    # whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#8B008B',
                    linewidth=1.5,
                    linestyle=":")

    # changing color and linewidth of
    # caps
    for cap in bp['caps']:
        cap.set(color='#8B008B',
                linewidth=2)

    # changing color and linewidth of
    # medians
    for median in bp['medians']:
        median.set(color='red',
                   linewidth=5)

    # changing style of fliers
    for flier in bp['fliers']:
        flier.set(marker='D',
                  color='#e7298a',
                  alpha=0.5)

    # Adding title
    # ax.set_title("Mean and standard deviation \n for different number of trials")
    ax.set_ylabel('Forged-origin prefix \n hijack success rate [%]')
    plt.xlabel("Number of trials [#]")

    # Removing top axes and right axes
    # ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

    plt.xticks([1, 2, 3, 4], ['10', '100', '1.000', '10.000'])
    #plt.yticks([0, 0.4, 0.8, 1.2, 1.6])

    fig.subplots_adjust(hspace=0.1)
    plt.ylim(5, 17)

    # show plot
    #plt.show()

    plt.savefig(filename + '.svg', format="svg")


def cumulative_roa_percentage(day):
    first_r = 0.007  # Daily growth rate for the first interval
    second_r = 0.01768  # Daily growth rate for the second interval
    second_period = 2750

    if day <= second_period:  # From July 1, 2012, to January 1, 2020
        # Calculate the cumulative percentage of ROAs created up to the given day
        cumulative_percentage = day * first_r
    else:  # After January 1, 2020
        # Calculate the cumulative percentage of ROAs created up to the given day
        cumulative_percentage = (day - second_period) * second_r + second_period * first_r

    return cumulative_percentage

def cumulative_rpki_percentage(day, start_date):
    cumulative_roa_value = cumulative_roa_percentage(day)
    #print(f"Up to day {day}, the cumulative percentage of ROAs created is approximately {cumulative_roa_value:.2f}%")

    remaining_days_to_rov_start = (date(2019,9,18)- start_date).days
    if day < remaining_days_to_rov_start:  # number of days between 1.7.2012 and 18.09.2019 (when ROV deployment started)
        cumulative_rov_percentage = 0
    else:
        adjusted_day = day - remaining_days_to_rov_start
        cumulative_rov_percentage = 0.0079 * adjusted_day
    #print(f"Up to day {day}, the cumulative percentage of ROV is approximately {cumulative_rov_percentage:.2f}%")
    return cumulative_roa_value, cumulative_rov_percentage

def get_rpki_history(start_date):
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

    # RPKI History line
    f_date = date(2012, 7, 1)  # Leave beginning as is!
    l_date = date(2023, 6, 1)
    delta = l_date - start_date

    rpki_history = np.zeros((delta.days, 2))
    cumulative_roa_value = np.zeros(delta.days)
    cumulative_rov_percentage = np.zeros(delta.days)

    for i in range(delta.days):
        cumulative_roa_value[i], cumulative_rov_percentage[i] = cumulative_rpki_percentage(i, start_date)
    return cumulative_roa_value, cumulative_rov_percentage


if __name__ == '__main__':

    #Figure 11
    filename = '/opt/simulation/bgpsim/outputs/figure11_ASPARandomDeployment_100x100x1000trials_seed8'
    #figure11(filename)

    #Figure 12
    filename = '/opt/simulation/bgpsim/outputs/figure12_ASPASelectiveDeployment_ObjectsTopToBottom_PolicyTopToBottom_100x100x1000trials_seed8'
    #figure11(filename)

    #Figure 13
    filename = '/opt/simulation/bgpsim/outputs/figure13_standard_deviation_10x100x1000x10000trials'
    #figure13(filename)

    #Figure 14
    filename = '/opt/simulation/bgpsim/outputs/figure14_ASPASelectiveDeployment_ObjectsBottomToTop_PolicyTopToBottom_100x100x100trials_Seed22'
    #figure11(filename)

    #Figure 15
    filename = '/opt/simulation/bgpsim/outputs/figure15_ASPASelectiveDeployment_ObjectsTopToBottom_PolicyTopToBottom_20x20x100trials_0.2sampling_seed8'
    #figure15(filename)

    #Figure 16
    filename = '/opt/simulation/bgpsim/outputs/figure16_ASPASelectiveDeployment_ObjectsTopToBottom_PolicyTopToBottom_30x30x1000trials_0.3sampling_seed8'
    #figure16(filename)

    #Figure 17
    filename = '/opt/simulation/bgpsim/outputs/figure17_ASPASelectiveDeployment_ObjectsBottomToTop_PolicyTopToBottom_5x100x1000trials_0.05sampling_seed8'
    #figure17(filename)

    #Figure 30
    filename = '/opt/simulation/bgpsim/outputs/figure30_ASCONESRandomDeployment_100x100x1000trials_seed8'
    #figure30(filename)

    #Figure 31
    filename = '/opt/simulation/bgpsim/outputs/figure31_ASCONESSelectiveDeployment_ObjectsTopToBottom_PolicyTopToBottom_100x100x1000trials_seed8'
    #figure30(filename)

    #Figure 32
    filename = '/opt/simulation/bgpsim/outputs/figure32_ASCONESSelectiveDeployment_ObjectsBottomToTop_PolicyTopToBottom_100x100x1000trials_seed8'
    #figure30(filename)

    #Figure 40
    filename = '/opt/simulation/bgpsim/outputs/figure40_ASPARandomDeployment_100x100x1000trials_seed8'
    #figure11(filename)

    #Figure 41
    filename = '/opt/simulation/bgpsim/outputs/figure41_standard_deviation_10x100x1000x10000trials'
    figure41(filename)

    #Figure 42
    filename = '/opt/simulation/bgpsim/outputs/figure42_ASPASelectiveDeployment_ObjectsTopToBottom_PolicyTopToBottom_100x100x1000trials_seed8'
    #figure11(filename)

    #Figure 43
    filename = '/opt/simulation/bgpsim/outputs/figure43_ASPASelectiveDeployment_ObjectsBottomToTop_PolicyTopToBottom_100x100x100trials_seed8'
    #figure11(filename)















