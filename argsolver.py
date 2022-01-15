import argparse

parser = argparse.ArgumentParser()
# parser.add_argument('--height', type=int, help='屏幕高度',default=2109)
# parser.add_argument('--width', type=int, help='屏幕宽度',default=3834)


parser.add_argument('--keydelay', help='按键延迟', type=float, default="0")
parser.add_argument('--stop', type=str, help='停止当前的功能', default="f11")
parser.add_argument('--allstop', help='关闭程序', type=str, default="delete")
parser.add_argument('--record', help='记录性能', type=str, default="f10")
parser.add_argument('--anaGear', help='手动', type=str, default="f9")
parser.add_argument('--handel', help='手离', type=str, default="f8")

# 注意!!! 改键去keyboardsim.py看一眼键盘码表全不全 不全的自己补一下
# 注意!!! 改键去keyboardsim.py看一眼键盘码表全不全 不全的自己补一下
# 注意!!! 改键去keyboardsim.py看一眼键盘码表全不全 不全的自己补一下
# 注意!!! 改键去keyboardsim.py看一眼键盘码表全不全 不全的自己补一下
# 注意!!! 改键去keyboardsim.py看一眼键盘码表全不全 不全的自己补一下

parser.add_argument('--clutch', type=str, help='离合按键', default="i")
parser.add_argument('--upgear', type=str, help='升档', default="e")
parser.add_argument('--downgear', type=str, help='降档', default="q")
parser.add_argument('--clutchBefore', type=float, help='踩下离合到换挡的延迟(秒)', default=0.1)
parser.add_argument('--clutchAfter', type=float, help='换挡到抬起离合的延迟(秒)', default=0.1)
parser.add_argument('--downGearCoolDown', type=float, help='降档的cd 连续降档间隔时长(秒)', default=0.5)
parser.add_argument('--upGearCoolDown', type=float, help='升档的cd 连续升档间隔时长(秒)', default=1)
parser.add_argument('--playerCoolDown', type=float, help='玩家介入换挡后程序发呆的时间(秒)', default=1)
# 降档时下面两条并行
# if accelAfterGearDown>0 按离合 sleep(accelBeforeGearDown) 按油门 sleep(accelAfterGearDown) 抬油门
# 按离合 sleep(clutchBefore) 换挡 sleep(clutchAfter) 抬油门
parser.add_argument('--accelAfterGearDown', type=float, help='降档补油时长 0是关闭(秒)', default=0)
parser.add_argument('--accelBeforeGearDown', type=float, help='从按下离合到启动降档补油的时长(秒)', default=0.05)
parser.add_argument('--accelKey', type=str, help='油门按键', default='w')
# 有人说后驱降档滑了
parser.add_argument('--minDownGear', type=int, help='最低降档降到的档位', default=1)
parser.add_argument('--minSpeed', type=int, help='当速度低于这个值时换挡系统不会工作', default=0)

parser.add_argument('--onlyDown', type=int, help='只降档不升档', default=0)
parser.add_argument('--speedGap', type=int, help='降档策略 当前档位速度小于 下一档位能触及的最高速度-speedGap时 降档', default=20)
parser.add_argument('--enablePlot', type=int, help='设置为0 关闭统计图表 用于兼容py39', default=1)

args = parser.parse_args()
