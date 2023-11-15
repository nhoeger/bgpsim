import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm


def evaluate(input: str, output: str, threshold: int) -> None:
    data = np.loadtxt(input, delimiter=',')
    area = []
    x = []
    y = []
    z = []
    length = (100/round(len(data) ** (1. / 3)-1))

    deploymentsTierThree = np.arange(0, 101, length)
    deploymentsTierTwo = reversed(np.arange(0, 101, length))
    deploymentsTierOne = np.arange(0, 101, length)

    for deployment2 in deploymentsTierTwo:
        for deployment in deploymentsTierThree:
            for deployment3 in deploymentsTierOne:
                area.append([deployment3, deployment, deployment2])

    for elements in area:
        x.append(elements[0])
    for elements in area:
        y.append(elements[2])
    for elements in area:
        z.append(elements[1])


    #Evaluate first bare figure
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.grid()
    image = ax.scatter(y, z, x, c=data, cmap=plt.cm.rainbow)
    cbar = fig.colorbar(image, shrink=0.6, pad=0.1)
    cbar.set_label('\n attacker-success-rate [%]')
    ax.set_xlabel('Tier Two deployment-rate [%]')
    ax.set_ylabel('Tier Three deployment-rate [%]')
    ax.set_zlabel('Tier One deployment-rate [%]')
    # ax.invert_xaxis()
    plt.savefig(output)

    #Cleanup data for second figure
    data_clean = []
    xClean = x
    yClean = y
    zClean = z
    count = 0

    newThreshold = (max(data)-min(data))/100*threshold

    for elements in data:
        if elements > newThreshold:
            xClean.pop(count)
            yClean.pop(count)
            zClean.pop(count)
            count = count - 1
        else:
            data_clean.append(elements)
        count = count + 1

    # Evaluate second cleaned figure
    fig2 = plt.figure(figsize=(11, 11))
    aNeu = fig2.add_subplot(111, projection='3d')
    aNeu.grid()
    imageNeu = aNeu.scatter(yClean, zClean, xClean, c=data_clean, cmap=plt.cm.rainbow)
    cBarNeu = fig2.colorbar(imageNeu, shrink=0.6, pad=0.1)
    cBarNeu.set_label('\n attacker-success-rate [%]')
    aNeu.set_title('Cleanup shows ' + str(threshold) + '% of all values \n with lowest attacker-success-rate')
    aNeu.set_xlabel('Tier Two deployment-rate [%]')
    aNeu.set_ylabel('Tier Three deployment-rate [%]')
    aNeu.set_zlabel('Tier One deployment-rate [%]')

    plt.savefig(output+'_cleanUp')

    print("Evaluation files stored at desired path.")