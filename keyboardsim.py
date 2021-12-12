import time
import ctypes
import win32api
import win32con
from argsolver import args
keycooldown = 0.001+args.keydelay
LEFT = 37
UP = 38
RIGHT = 39
DOWN = 40
ENTER = 13

LEFT = 65
DOWN = 83
UP = 87
RIGHT = 68

# keybind不全 想要额外的下面自己补一下
# keybind不全 想要额外的下面自己补一下
# keybind不全 想要额外的下面自己补一下
# keybind不全 想要额外的下面自己补一下
keybind = {
    "up": UP,
    "left": LEFT,
    "down": DOWN,
    "right": RIGHT,
    'enter': ENTER,
    "esc": 27,
    'tab':9,
    'q':81,
    'e':69,
    'i':73,
    'shift':16,
    'w': 87,
}

# A	65	J	74	S	83	1	49
# B	66	K	75	T	84	2	50
# C	67	L	76	U	85	3	51
# D	68	M	77	V	86	4	52
# E	69	N	78	W	87	5	53
# F	70	O	79	X	88	6	54
# G	71	P	80	Y	89	7	55
# H	72	Q	81	Z	90	8	56
# I	73	R	82	0	48	9	57
# 数字键盘上的键的键码值(keyCode)	功能键键码值(keyCode)
# 按键	键码	按键	键码	按键	键码	按键	键码
# 0	96	8	104	F1	112	F7	118
# 1	97	9	105	F2	113	F8	119
# 2	98	*	106	F3	114	F9	120
# 3	99	+	107	F4	115	F10	121
# 4	100	Enter	108	F5	116	F11	122
# 5	101	-	109	F6	117	F12	123
# 6	102	.	110
# 7	103	/	111
# 控制键键码值(keyCode)
# 按键	键码	按键	键码	按键	键码	按键	键码
# BackSpace	8	Esc	27	Right Arrow	39	-_	189
# Tab	9	Spacebar	32	Dw Arrow	40	.>	190
# Clear	12	Page Up	33	Insert	45	/?	191
# Enter	13	Page Down	34	Delete	46	`~	192
# Shift	16	End	35	Num Lock	144	[{	219
# Control	17	Home	36	;:	186	/|	220
# Alt	18	Left Arrow	37	=+	187	]}	221
# Cape Lock	20	Up Arrow	38	,<	188	'"	222




def press(key, cooldown=keycooldown):
    MapKey = ctypes.windll.user32.MapVirtualKeyA
    win32api.keybd_event(key, MapKey(key, 0), 0, 0)
    time.sleep(cooldown)
    win32api.keybd_event(key, MapKey(key, 0), win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(cooldown)

def pressdown_str(keystr,cooldown=keycooldown):
    key=keybind[keystr]
    MapKey = ctypes.windll.user32.MapVirtualKeyA
    win32api.keybd_event(key, MapKey(key, 0), 0, 0)
    time.sleep(cooldown)
def pressup_str(keystr,cooldown=keycooldown):
    key=keybind[keystr]
    MapKey = ctypes.windll.user32.MapVirtualKeyA
    win32api.keybd_event(key, MapKey(key, 0), win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(cooldown)


def press_str(keystr,**kwargs):
    press(keybind[keystr],**kwargs)


if __name__ == "__main__":
    pass
    # time.sleep(1)
    # press(72)
    # import pyautogui
    #
    # pyautogui.moveTo(x=100, y=100, duration=2, tween=pyautogui.linear)
    # pyautogui.press('esc')
