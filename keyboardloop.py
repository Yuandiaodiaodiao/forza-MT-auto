from concurrent.futures import ThreadPoolExecutor, wait

from argsolver import args
from logger import logger

threadPool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="exec")
from pynput.keyboard import Listener
from keyboardsim import press_str
import os
import time
import threading
import numpy as np
import matplotlib.pyplot as plt

def get_key_name(key):
    t = None
    try:
        t = key.char
    except:
        try:
            t = key.name
        except:
            return ""
    return t


def get_thread_id(thread):
    for id, t in threading._active.items():
        if t is thread:
            return id


def raise_exception(thread_id):
    import ctypes
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                     ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print('Exception raise failure')




def stop():
    global threadPool
    for thread in threadPool._threads:
        id = get_thread_id(thread)
        raise_exception(id)

    threadPool.shutdown(wait=False)


def restart():
    global threadPool
    stop()
    threadPool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="exec")


from listen import ForzaControl

control = ForzaControl()


def presskey(key):
    global threadPool
    global control
    t = get_key_name(key)

    if t == args.record:
        print('f10 record')
        if control.isRun:
            print('stop')
            if len(control.recordList)>3:
                ls=list(control.recordList)
                stop()
                rpm=np.array([item.get('rpm') for index,item in enumerate(ls)])
                gear=np.array([item.get('gear')*1000 for index,item in enumerate(ls)])
                time=np.array([item.get('time') for index,item in enumerate(ls)])
                speed=np.array([item.get('speed')*10 for index,item in enumerate(ls)])
                slip=np.array([item.get('slip')*1000 for index,item in enumerate(ls)])
                clutch=np.array([item.get('clutch')*10 for index,item in enumerate(ls)])
                power=np.array([item.get('power')*10 for index,item in enumerate(ls)])
                time0=ls[0].get('time')
                time=np.where(time>0,time-time0,0)
                plt.plot(time,rpm,label='rpm')
                plt.plot(time,gear,label='gear')
                plt.plot(time,speed,label='speed')
                plt.plot(time,slip,label='slip')
                plt.plot(time,clutch,label='clutch')
                plt.plot(time,power,label='power')
                plt.legend()
                plt.xticks(np.arange(0,time[-1],0.5))
                plt.show()
                control.isRun=False
                import json
                json.dump(ls,open('record.json','w',encoding='utf-8'))
                # 分析换挡时机
                from analyze import solveGearControlLs
                gearls=solveGearControlLs(ls)
                control.gearLs=gearls
            restart()
            control.isRun=False
        else:
            print('submit')
            def run():
                control.run(mode='record')
                print('执行完成')
            threadPool.submit(run)

    elif t == args.anaGear:
        print('f9 ana')
        if control.isRun:
            print('restart')
            control.isRun=False
            restart()
        else:
            print('anaGear')
            def run():
                control.run(mode='anaGear')
                print('执行完成')

            threadPool.submit(run)


    elif t == args.stop:
        # 停止当前的动作
        logger.info("stop")
        restart()

    elif t == args.allstop:
        # 停止进程
        stop()
        exit(0)
        raise Exception


if __name__ == '__main__':
    logger.info("start!")

    with Listener(on_press=presskey) as listener:
        listener.join()
