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
            print('录制已停止')
            if len(control.recordList)>3:
                ls=list(control.recordList)
                stop()
                control.isRun=False
                import json
                car_ordinal=ls[0]['car_ordinal']
                try:
                    import os
                    os.mkdir('cars')
                except:
                    pass
                carPath=f'./cars/record_{car_ordinal}.json'
                print(f'本次起跑数据已保存到{carPath}')
                json.dump(ls,open(carPath,'w',encoding='utf-8'))
                # 分析换挡时机
                from analyze import solveGearControlLs
                gearls=solveGearControlLs(ls)
                control.gearLs=gearls
                print('录制完成 f9手动 f8手离')
            restart()
            control.isRun=False
        else:
            print('submit')
            def run():
                control.run(mode='record')
                print('录制异常退出')
            threadPool.submit(run)

    elif t == args.anaGear:
        print('f9 ana')
        if control.isRun:
            print('自动换挡已停止')
            control.isRun=False
            restart()
        else:
            print('anaGear')
            def run():
                print('手动档启动')
                control.isHandle=False
                control.run(mode='anaGear')
                print('手动档异常退出')

            threadPool.submit(run)
    elif t == args.handel:
        print('f8 handel ana')
        if control.isRun:
            print('自动换挡已停止')
            control.isRun=False
            restart()
        else:
            print('anaGear')
            def run():
                print('手离启动')
                control.isHandle=True
                control.run(mode='anaGear')
                print('手离异常退出')

            threadPool.submit(run)

    elif t == args.stop:
        # 停止当前的动作
        logger.info("stop")
        control.isRun=False
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
