#!/usr/env/python
# -*- coding: utf-8 -*-
'''
Script to listen on a given port for UDP packets sent by a Forza Motorsport 7
"data out" stream and write the data to a TSV file.

Copyright (c) 2018 Morten Wang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
from concurrent.futures.thread import ThreadPoolExecutor

from argsolver import args
import csv
import logging
import socket
import time
import yaml
import datetime as dt

from fdp import ForzaDataPacket
from keyboardsim import press_str, pressup_str, pressdown_str
from math import floor
import queue


def to_str(value):
    '''
    Returns a string representation of the given value, if it's a floating
    number, format it.

    :param value: the value to format
    '''
    if isinstance(value, float):
        return ('{:f}'.format(value))

    return ('{}'.format(value))


from functools import wraps


def trycatch(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        try:

            return func(*args, **kwargs)
        except Exception as e:
            print('出错了')
            print(e)
            raise e
            print(str(e))

    return with_logging


import threading


class StopableThredPool:

    def __init__(self):
        self.running=False
        self.threadPool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="execx")

    def stop(self):

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

        for thread in self.threadPool._threads:
            id = get_thread_id(thread)
            raise_exception(id)

        self.threadPool.shutdown(wait=False)

    def restart(self):
        self.stop()
        self.threadPool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="exec")


class ForzaControl:
    def __init__(self):
        self.isRun = False
        self.isHandle = False
        self.gearLs = []
        self.recordList = []
        self.threadPool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="exec")
        self.messageThread = StopableThredPool()
        self.fdpQueue = queue.Queue(maxsize=0)

        pass

    def run(self, mode):
        print(f'run {mode} 手动挡{self.isHandle}')
        self.isRun = True
        self.mode = mode
        self.main()

    def main(self):
        import argparse

        cli_parser = argparse.ArgumentParser(
            description="script that grabs data from a Forza Motorsport stream and dumps it to a TSV file"
        )

        # Verbosity option
        cli_parser.add_argument('-v', '--verbose', action='store_true',
                                help='write informational output')

        cli_parser.add_argument('-a', '--append', action='store_true',
                                default=False, help='if set, data will be appended to the given file')

        cli_parser.add_argument('-f', '--format', type=str, default='tsv',
                                choices=['tsv', 'csv'],
                                help='what format to write out, "tsv" means tab-separated, "csv" comma-separated; default is "tsv"')

        cli_parser.add_argument('-p', '--packet_format', type=str, default='dash',
                                choices=['sled', 'dash', 'fh4'],
                                help='what format the packets coming from the game is, either "sled", "dash", or "fh4"')

        cli_parser.add_argument('-c', '--config_file', type=str,
                                help='path to the YAML configuration file')

        args = cli_parser.parse_args()

        if args.verbose:
            logging.basicConfig(level=logging.INFO)

        self.dump_stream(5300, 'test.txt', args.format, args.append,
                         args.packet_format, args.config_file)

    def dump_stream(self, port, output_filename, format='tsv',
                    append=False, packet_format='dash', config_file=None):
        '''
        Opens the given output filename, listens to UDP packets on the given port
        and writes data to the file.

        :param port: listening port number
        :type port: int

        :param output_filename: path to the file we will write to
        :type output_filename: str

        :param format: what format to write out, either 'tsv' or 'csv'
        :type format: str

        :param append: if set, the output file will be opened for appending and
                       the header with column names is not written out
        :type append: bool

        :param packet_format: the packet format sent by the game, one of either
                              'sled' or 'dash'
        :type packet_format str

        :param config_file: path to the YAML configuration file
        :type config_file: str
        '''
        if self.messageThread.running == False:
            if config_file:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)

                ## The configuration can override everything
                if 'port' in config:
                    port = config['port']

                if 'output_filename' in config:
                    output_filename = config['output_filename']

                if 'format' in config:
                    format = config['format']

                if 'append' in config:
                    append = config['append']

                if 'packet_format' in config:
                    packet_format = config['packet_format']

            params = ForzaDataPacket.get_props(packet_format=packet_format)
            if config_file and 'parameter_list' in config:
                params = config['parameter_list']

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind(('', port))

            logging.info('listening on port {}'.format(port))
            self.packet_format = packet_format

            print('初始化消息队列')
            # self.messageThread.restart()
            # time.sleep(1)
            def getFdp():
                print('get Fdp thread启动')
                while True:
                    message, address = self.server_socket.recvfrom(1024)
                    fdp = ForzaDataPacket(message, packet_format=self.packet_format)
                    self.last_car_ordinal=fdp.car_ordinal or self.last_car_ordinal
                    if self.fdpQueue.qsize() > 10:
                        self.fdpQueue.get()
                    self.fdpQueue.put(fdp)


        # 启动消息队列
            self.messageThread.threadPool.submit(getFdp)
            self.messageThread.running=True


        if self.mode == 'record':
            print('record ready!! 请起跑')
            self.record()
        if self.mode == 'anaGear':
            print('自动换挡 启动')
            self.anaGear()



    @trycatch
    def record(self):
        self.recordList = []
        stop = True
        while True:

            fdp = self.getFdp()
            # print(f'RL={fdp.tire_slip_ratio_RL} speed={fdp.speed}')
            if fdp.tire_slip_ratio_RL > 0.01 or fdp.speed > 0.01:
                stop = False
            if stop:
                continue
            self.recordList.append({
                'gear': fdp.gear,
                'rpm': fdp.current_engine_rpm,
                'time': time.time(),
                'speed': fdp.speed * 3.6,
                'slip': min(1.1, (fdp.tire_slip_ratio_RL + fdp.tire_slip_ratio_RR) / 2),
                'clutch': fdp.clutch,
                'power': fdp.power / 1000,
                'car_ordinal': fdp.car_ordinal,
            })

    def getFdp(self):
        while self.fdpQueue.qsize() > 1:
            self.fdpQueue.get()
        return self.fdpQueue.get()

    def upGearHandle(self):

        pressdown_str(args.clutch, cooldown=args.clutchBefore)
        press_str(args.upgear)
        time.sleep(args.clutchAfter)
        pressup_str(args.clutch)

    def upGear(self):
        press_str(args.upgear)

    def downGearHandle(self,enableDownAcc=True):
        self.downAcc(enableDownAcc)
        pressdown_str(args.clutch, cooldown=args.clutchBefore)

        press_str(args.downgear)

        time.sleep(args.clutchAfter)
        pressup_str(args.clutch)
    def downAcc(self,enableDownAcc=True):
        if enableDownAcc==True and args.accelAfterGearDown > 0:
            def downAcc():
                print('降档补油')
                # 是降档 补油
                pressdown_str(args.accelKey)
                time.sleep(args.accelAfterGearDown)
                pressup_str(args.accelKey)
            self.threadPool.submit(downAcc)
    def downGear(self,enableDownAcc=True):
        self.downAcc(enableDownAcc)
        press_str(args.downgear)

    def autoUp(self):
        if self.isHandle:
            self.upGearHandle()
        else:
            self.upGear()

    def autoDown(self,enableDownAcc=True):
        if self.isHandle:
            self.downGearHandle(enableDownAcc)
        else:
            self.downGear(enableDownAcc)

    def loadGearlsFromFile(self, car_ordinal):
        from analyze import solveGearControlLs
        import json
        carPath = f'./cars/record_{car_ordinal}.json'

        print(f'从{carPath} 加载起跑数据开始分析')
        try:

            ls = json.load(open(carPath, 'r', encoding='utf-8'))
            gearls = solveGearControlLs(ls)
            self.gearLs = gearls
            print('分析完成')
        except Exception as e:
            if car_ordinal == 0:
                print('找不到车辆id 若请确认车开在街上')
            else:
                print('未找到车辆起跑数据 请按照readme.md 按f10进行起步测试')
            raise e

    @trycatch
    def anaGear(self):

        fdp = self.getFdp()
        car_ordinal = self.last_car_ordinal or fdp.car_ordinal
        self.loadGearlsFromFile(car_ordinal)

        print('load cache')

        targetGear = fdp.gear
        lastGear = 0
        coolDownLock = time.time()
        gearLs = self.gearLs
        manyDown = False
        while True:
            fdp = self.getFdp()
            speed = fdp.speed * 3.6
            gear = fdp.gear
            rpm = fdp.current_engine_rpm
            accel = fdp.accel
            # 没起车不处理
            # if gear == 0: continue
            # 过长时间没有动作就同步档位
            if time.time() - coolDownLock > 2:
                # 换挡同步
                targetGear = gear
            # 检测到换挡
            if manyDown:

                if gear > targetGear:
                    self.autoDown(False)
                    sleepTime=0.05
                    if gear<=3:
                        sleepTime=0.3
                    time.sleep(sleepTime)
                    continue
                elif gear <= 0:
                    self.autoUp()
                    manyDown = False
                    continue
                manyDown = False

            if gear != lastGear:
                print('gearChange')
                if targetGear == gear:
                    # 自动换挡成功

                    pass
                else:
                    # 是用户手动换挡的
                    # 同步档位 加cooldown
                    coolDownLock = time.time() + args.playerCoolDown
                    targetGear = gear
            lastGear = gear
            gearfix = gear

            # 低速不处理
            if speed < args.minSpeed:
                continue
            # 用户挂倒档了 不管
            if gear <= 0: continue

            mode = 'auto'
            # 低于档位最低速度的策略 kmh
            speedGap = args.speedGap
            if mode == 'auto':
                try:

                    gearNowConfig = next(item for item in gearLs if item['gear'] == gear)
                    slip = (fdp.tire_slip_ratio_RL + fdp.tire_slip_ratio_RR) / 2
                    # 没滑并且到转速 并且踩油门 升档
                    # print(f'acc={accel} rpm={rpm} targetRpm={gearNowConfig["rpm"]}')
                    if rpm > gearNowConfig['rpm'] * 0.99 and slip < 1 and accel > 100:
                        gearfix = gear + 1
                    elif speed > gearNowConfig['speed']:
                        # 速度超过了 升档
                        gearfix = gear + 1
                except:
                    pass
                if gear > 1:
                    gearLowConfig = None
                    for i in range(1, 10):
                        try:
                            gearLowConfig = next(item for item in gearLs if item['gear'] == gear - i)
                            if speed + speedGap < gearLowConfig['speed']:
                                gearfix = gear - i
                        except:
                            pass
                    if gearLowConfig is None:
                        print('降档策略执行失败')

            cooldownup = args.upGearCoolDown
            cooldowndown = args.downGearCoolDown

            while gearfix != gear and gear == targetGear:
                if time.time() < coolDownLock:
                    break
                if gear < gearfix:
                    if args.onlyDown != 1:
                        self.autoUp()
                    print(f'up gear={gear} fix={gearfix} rpm={rpm}%')
                    coolDownLock = time.time() + cooldownup

                    targetGear = gear + 1
                elif gear > gearfix >= args.minDownGear:
                    # 降档多次
                    if gear - gearfix > 1 and gearfix == 1:
                        gearfix = 2
                    if gear - gearfix > 1:
                        manyDown = True
                        print(f'连续降档*{gear - gearfix}')

                    self.autoDown()
                    print(f'down gear={gear} fix={gearfix} rpm={rpm}%')
                    coolDownLock = time.time() + cooldowndown

                    targetGear = gearfix


if __name__ == "__main__":
    control = ForzaControl()
    control.run()
