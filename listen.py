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

import csv
import logging
import socket
import time
import yaml
import datetime as dt

from fdp import ForzaDataPacket
from keyboardsim import press_str, pressup_str, pressdown_str
from math import floor


def to_str(value):
    '''
    Returns a string representation of the given value, if it's a floating
    number, format it.

    :param value: the value to format
    '''
    if isinstance(value, float):
        return ('{:f}'.format(value))

    return ('{}'.format(value))


class ForzaControl:
    def __init__(self):
        self.isRun = False
        self.isHandle=False
        self.gearLs=[]
        self.recordList=[]
        pass

    def run(self, mode='autoGear'):
        print(f'run{mode}')
        self.isRun = True
        self.mode = mode
        print(f'run{mode}')
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
        message, address = self.server_socket.recvfrom(1024)
        fdp = ForzaDataPacket(message, packet_format=self.packet_format)
        print('ready!!')
        if self.mode == 'autoGear':
            self.autoGear()
        if self.mode == 'record':
            self.record()
        if self.mode == 'anaGear':
            self.anaGear()

    def autoGear(self):
        message, address = self.server_socket.recvfrom(1024)
        fdp = ForzaDataPacket(message, packet_format=self.packet_format)
        self.fdp = fdp
        self.targetGear = fdp.gear
        self.lastGear = 0
        self.lastCoolDown = time.time()
        while True:
            message, address = self.server_socket.recvfrom(1024)
            self.fdp = ForzaDataPacket(message, packet_format=self.packet_format)
            fdp = self.fdp
            self.speed = fdp.speed * 3.6
            self.gear = fdp.gear
            if self.mode == 'autoGear':
                self.autoGear()
            if self.mode == 'record':
                self.record()

            gears = [[], [0, 50], [45, 80], [72, 105], [97, 125], [117, 145], [137, 170], [163, 199], [193, 220]]
            speed = self.speed

            gear = fdp.gear
            if gear == 0: return
            if time.time() - self.lastCoolDown > 1:
                # 换挡同步
                self.targetGear = gear
            if gear != self.lastGear:
                print('gearChange')
                if self.targetGear == gear:
                    # 换挡成功
                    pass
                else:
                    # 同步档位 加cooldown
                    self.targetGear = gear
            self.lastGear = gear
            gearfix = gear

            maxrpm = fdp.engine_max_rpm + 1
            rpm = fdp.current_engine_rpm
            rpmp = rpm / maxrpm * 100
            print(f'{floor(rpm / maxrpm * 100)}% {rpm} {maxrpm}')
            # continue
            if self.targetGear == 0:
                self.targetGear = 1
            if speed < 10:
                return
            if gear <= 0: return

            # print(f' gear={gear} fix={gearfix} target={self.targetGear}')
            mode = 'rpm'
            cooldownt = 1
            if mode == 'rpmp':
                rpms = [[], [0, 90], [55, 90], [60, 90], [60, 90], [60, 90], [60, 90], [60, 90], [60, 90], [60, 90],
                        [60, 100]]
                if rpms[gear][0] < rpmp < rpms[gear][1]:
                    gearfix = gear
                    pass
                else:
                    for i in range(1, len(rpms)):
                        [l, h] = rpms[i]
                        # print(f'{l}<{h}')
                        if l < rpmp < h:
                            gearfix = i
                            # print(f'fix{i}')
                            break
            elif mode == 'rpm':
                rpms = [[], [-10, 74], [53, 76], [60, 78], [60, 78], [60, 78], [60, 78], [60, 78], [60, 78],
                        [60, 78]]
                if rpms[gear][0] < rpm / 100 < rpms[gear][1]:
                    gearfix = gear
                    # print('pass')
                    pass
                else:
                    if rpm / 100 > rpms[gear][1]:
                        gearfix = gear + 1
                    elif rpm / 100 < rpms[gear][0]:
                        gearfix = gear - 1


            else:
                if gears[gear][0] < speed < gears[gear][1]:
                    gearfix = gear
                    pass
                else:
                    for i in range(1, len(gears)):
                        [l, h] = gears[i]
                        # print(f'{l}<{h}')
                        if l < speed < h:
                            gearfix = i
                            # print(f'fix{i}')
                            break
            while gearfix != gear and gear == self.targetGear:
                if time.time() - self.lastCoolDown < cooldownt:
                    # print('jump')
                    break
                self.lastCoolDown = time.time()
                if gear < gearfix:
                    pressdown_str('i', cooldown=0.1)
                    press_str('e')
                    time.sleep(0.1)

                    pressup_str('i')
                    print(f'up gear={gear} fix={gearfix} rpm={rpmp}%')

                    gear += 1
                    self.targetGear = gear
                else:
                    pressdown_str('i', cooldown=0.1)
                    press_str('q')
                    time.sleep(0.1)
                    pressup_str('i')
                    print(f'down gear={gear} fix={gearfix} rpm={rpmp}%')

                    gear -= 1
                    self.targetGear = gear

    def record(self):
        self.recordList = []
        stop = True
        while True:
            message, address = self.server_socket.recvfrom(1024)
            fdp = ForzaDataPacket(message, packet_format=self.packet_format)
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
            })

    def getFdp(self):
        message, address = self.server_socket.recvfrom(1024)
        fdp = ForzaDataPacket(message, packet_format=self.packet_format)
        return fdp

    def upGearHandle(self):
        pressdown_str('i', cooldown=0.1)
        press_str('e')
        time.sleep(0.1)
        pressup_str('i')

    def upGear(self):
        press_str('e')

    def downGearHandle(self):
        pressdown_str('i', cooldown=0.1)
        press_str('q')
        time.sleep(0.1)
        pressup_str('i')

    def downGear(self):
        press_str('q')

    def autoUp(self):
        if self.isHandle:
            self.upGearHandle()
        else:
            self.upGear()

    def autoDown(self):
        if self.isHandle:
            self.downGearHandle()
        else:
            self.downGear()

    def loadGearlsFromFile(self):
        from analyze import solveGearControlLs
        import json
        ls = json.load(open('record.json', 'r', encoding='utf-8'))
        gearls = solveGearControlLs(ls)
        self.gearLs = gearls

    def anaGear(self):
        if len(self.gearLs)==0:
            self.loadGearlsFromFile()
            print('load cache')

        fdp = self.getFdp()
        targetGear = fdp.gear
        lastGear = 0
        coolDownLock=time.time()
        gearLs = self.gearLs
        while True:
            fdp = self.getFdp()
            speed = fdp.speed * 3.6
            gear = fdp.gear
            rpm = fdp.current_engine_rpm
            accel = fdp.accel
            # 没起车不处理
            if gear == 0: continue
            # 过长时间没有动作就同步档位
            if time.time() - coolDownLock > 2:
                # 换挡同步
                targetGear = gear
            # 检测到换挡
            if gear != lastGear:
                print('gearChange')
                if targetGear == gear:
                    # 自动换挡成功
                    pass
                else:
                    # 是用户手动换挡的
                    # 同步档位 加cooldown
                    coolDownLock=time.time()+5
                    targetGear = gear
            lastGear = gear
            gearfix = gear

            # 低速不处理
            if speed < 10:
                continue
            # 用户挂倒档了 不管
            if gear <= 0: continue

            mode = 'auto'
            # 预期的换挡时间
            speedGap = 10
            if mode == 'auto':
                try:

                    gearNowConfig = next(item for item in gearLs if item['gear'] == gear)
                    slip = (fdp.tire_slip_ratio_RL + fdp.tire_slip_ratio_RR) / 2
                    # 没滑并且到转速 并且踩油门 升档
                    # print(f'acc={accel} rpm={rpm} targetRpm={gearNowConfig["rpm"]}')
                    if rpm > gearNowConfig['rpm']*0.99 and slip < 1 and accel > 100:
                        gearfix = gear + 1
                    elif speed > gearNowConfig['speed']:
                        # 速度超过了 升档
                        gearfix = gear + 1
                except:
                    pass
                if gear > 1:
                    gearLowConfig = next(item for item in gearLs if item['gear'] == gear - 1)
                    # 按速度降档 转速可以不管
                    if speed + speedGap < gearLowConfig['speed']:
                        gearfix = gear - 1
            cooldownup = 1
            cooldowndown = 0.5

            while gearfix != gear and gear == targetGear:
                if time.time()<coolDownLock:
                    break
                if gear < gearfix:
                    self.autoUp()
                    print(f'up gear={gear} fix={gearfix} rpm={rpm}%')
                    coolDownLock = time.time()+cooldownup

                    gear += 1
                    targetGear = gear
                else:
                    self.autoDown()
                    print(f'down gear={gear} fix={gearfix} rpm={rpm}%')
                    coolDownLock = time.time()+cooldowndown

                    gear -= 1
                    targetGear = gear


if __name__ == "__main__":
    control = ForzaControl()
    control.run()
