
# print(js)


def drawLs(ls,startT,endT):
    import numpy as np
    import matplotlib.pyplot as plt

    ls = list(ls)
    rpm = np.array([item.get('rpm') for index, item in enumerate(ls)])
    gear = np.array([item.get('gear') * 1000 for index, item in enumerate(ls)])
    time = np.array([item.get('time') for index, item in enumerate(ls)])
    speed = np.array([item.get('speed') * 10 for index, item in enumerate(ls)])
    slip = np.array([item.get('slip') * 1000 for index, item in enumerate(ls)])
    clutch = np.array([item.get('clutch') * 10 for index, item in enumerate(ls)])
    power = np.array([item.get('power') * 10 for index, item in enumerate(ls)])
    time0 = startT
    time = np.where(time > 0, time - time0, 0)
    plt.rcParams['savefig.dpi']=500
    plt.rcParams['figure.dpi']=500
    plt.plot(time, rpm, label='rpm')
    plt.plot(time, gear, label='gear',color='k')
    plt.plot(time, speed, label='speed')
    plt.plot(time, slip, label='slip')
    # plt.plot(time, clutch, label='clutch')
    plt.plot(time, power, label='power',color='#FFDE39',linewidth=0.5)

    plt.legend()
    plt.xticks(np.arange(0, endT-startT, 1))
    plt.yticks(np.arange(0, 11000, 1000))
    plt.ylim(-500,11000)
    plt.show()


# 找到换挡时机
def genGearLs(ls):
    drawLs(ls, ls[0]['time'], ls[-1]['time'])
    try:
        zeroTime = next(item for item in ls if item['speed'] > 0.001)
        hunTime = next(item for item in ls if item['speed'] > 100)
        from math import floor
        print(f'0~100 {floor((hunTime["time"] - zeroTime["time"]) * 1000) / 1000}s')
    except:
        pass
    gearLs = []
    for index in range(1, len(ls) - 1):
        item = ls[index]
        item['index'] = index
        if ls[index].get('gear') != ls[index + 1].get('gear'):
            item['next'] = ls[index + 1].get('gear')
            gearLs.append(item)
            ls[index] = item
    return gearLs
# 向前连续一段时间找全部符合要求的
# 找到换挡时机之前最好的启动换挡机会
def genGearControlLs(ls,gearLs):
    gearControlLs = []
    for gearItem in gearLs:
        lastIndex = gearItem['index']

        def findLastPower():
            window = 15
            step = 5
            nowStep = 0
            while True:
                rangeL = [lastIndex - window - step * nowStep, lastIndex - step * nowStep]
                newRegion = ls[rangeL[0]:rangeL[1]]
                res = all(map(lambda x: x['power'] > 0, newRegion))
                # drawLs(newRegion, ls[0]['time'])
                # drawLs(newRegion, ls[0]['time'], ls[-1]['time'])

                if res:
                    # print('find')
                    # print(newRegion[0])
                    lastPIndex = newRegion[-1]['index']
                    avgPower = sum(map(lambda x: x['power'], newRegion)) / len(newRegion)
                    while ls[lastPIndex]['power'] > avgPower * 0.9 and ls[lastPIndex]['gear']==gearItem['gear']:
                        lastPIndex += 1
                    global powerLast
                    powerLast = ls[lastPIndex]
                    # drawLs(ls[lastPIndex - window:lastPIndex], ls[0]['time'], ls[-1]['time'])
                    return powerLast
                    break
                nowStep += 1

        powerLast=findLastPower()

        # powerLast 代表最大换挡功率的位置
        maxRpm = powerLast['rpm']
        gearSpeed = powerLast['speed']
        print(f'gear={powerLast["gear"]}maxRpm={maxRpm} speed={gearSpeed}')
        gearControlLs.append(powerLast)
    return gearControlLs
def solveGearControlLs(ls):
    gearLs = genGearLs(ls)
    controlLs = genGearControlLs(ls, gearLs)
    return controlLs
if __name__=='__main__':
    import json

    ls = json.load(open('record.json', 'r', encoding='utf-8'))
    # ls=ls[:200]
    # drawLs(ls, ls[0]['time'], ls[-1]['time'])

    cls=solveGearControlLs(ls)