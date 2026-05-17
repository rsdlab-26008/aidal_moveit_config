#!/usr/bin/env python3

import sys
import threading

import geometry_msgs.msg
import std_msgs.msg
import rclpy

from rclpy.node import Node

if sys.platform == 'win32':
    import msvcrt
else:
    import termios
    import tty


msg = """
This node takes keypresses from the keyboard and publishes them
as Twist messages. It works best with a us keyboard layout.
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

For Holonomic mode (strafing), hold down the shift key:
---------------------------
   U    I    O
   J    K    L
   M    <    >

t : up (+z)
b : down (-z)

Lift control:
   r : lift up
   f : lift down

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

CTRL-C to quit
"""

moveBindings = {
    'i': (1, 0, 0, 0),
    'o': (1, 0, 0, -1),
    'j': (0, 0, 0, 1),
    'l': (0, 0, 0, -1),
    'u': (1, 0, 0, 1),
    ',': (-1, 0, 0, 0),
    '.': (-1, 0, 0, 1),
    'm': (-1, 0, 0, -1),
    'O': (1, -1, 0, 0),
    'I': (1, 0, 0, 0),
    'U': (1, 1, 0, 0),
    'L': (0, -1, 0, 0),
    'J': (0, 1, 0, 0),
    'M': (-1, 1, 0, 0),
    '<': (-1, 0, 0, 0),
    '>': (-1, -1, 0, 0),
    't': (0, 0, 1, 0),
    'b': (0, 0, -1, 0),
}

speedBindings = {
    'q': (1.1, 1.1),
    'z': (.9, .9),
    'w': (1.1, 1),
    'x': (.9, 1),
    'e': (1, 1.1),
    'c': (1, .9),
}

# リフト設定
LIFT_MIN  = 0.1   # リフトの最小位置 [m]
LIFT_MAX  = 0.7   # リフトの最大位置 [m]
LIFT_STEP = 0.005  # 1キー入力あたりの移動量 [m]


def getKey(settings):
    if sys.platform == 'win32':
        return msvcrt.getch().decode('utf-8')
    tty.setraw(sys.stdin.fileno())
    select_timeout = 0.1
    import select
    rlist, _, _ = select.select([sys.stdin], [], [], select_timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed, turn):
    return 'currently:\tspeed %s\tturn %s ' % (speed, turn)


def main():
    settings = None
    if sys.platform != 'win32':
        settings = termios.tcgetattr(sys.stdin)

    rclpy.init()

    node = rclpy.create_node('teleop_twist_keyboard')

    pub      = node.create_publisher(geometry_msgs.msg.Twist, 'cmd_vel', 10)
    lift_pub = node.create_publisher(std_msgs.msg.Float64MultiArray, 'lift_controller/commands', 10)

    speed    = 0.5
    turn     = 1.0
    x        = 0.0
    y        = 0.0
    z        = 0.0
    th       = 0.0
    status   = 0.0
    lift_pos = 0.455  # リフトの現在位置 [m]

    try:
        print(msg)
        print(vels(speed, turn))
        while True:
            key = getKey(settings)

            # ===== リフト制御 =====
            if key == 'r':
                lift_pos = min(lift_pos + LIFT_STEP, LIFT_MAX)
                lift_msg = std_msgs.msg.Float64MultiArray()
                lift_msg.data = [lift_pos]
                lift_pub.publish(lift_msg)
                print(f'lift_joint: {lift_pos:.3f} m  (max: {LIFT_MAX} m)')
                continue
            elif key == 'f':
                lift_pos = max(lift_pos - LIFT_STEP, LIFT_MIN)
                lift_msg = std_msgs.msg.Float64MultiArray()
                lift_msg.data = [lift_pos]
                lift_pub.publish(lift_msg)
                print(f'lift_joint: {lift_pos:.3f} m  (min: {LIFT_MIN} m)')
                continue

            # ===== 移動制御 =====
            elif key in moveBindings.keys():
                x  = moveBindings[key][0]
                y  = moveBindings[key][1]
                z  = moveBindings[key][2]
                th = moveBindings[key][3]
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn  = turn  * speedBindings[key][1]

                print(vels(speed, turn))
                if (status == 14):
                    print(msg)
                status = (status + 1) % 15
            else:
                x  = 0.0
                y  = 0.0
                z  = 0.0
                th = 0.0
                if (key == '\x03'):
                    break

            twist = geometry_msgs.msg.Twist()
            twist.linear.x  = x * speed
            twist.linear.y  = y * speed
            twist.linear.z  = z * speed
            twist.angular.x = 0.0
            twist.angular.y = 0.0
            twist.angular.z = th * turn
            pub.publish(twist)

    except Exception as e:
        print(e)

    finally:
        twist = geometry_msgs.msg.Twist()
        twist.linear.x  = 0.0
        twist.linear.y  = 0.0
        twist.linear.z  = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0
        pub.publish(twist)

        if sys.platform != 'win32':
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == '__main__':
    main()
