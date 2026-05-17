import sys
import math
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class GripperClient(Node):
    def __init__(self):
        super().__init__('gripper_client')

        self.left_action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/left_gripper_controller/follow_joint_trajectory'
        )

        self.right_action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/right_gripper_controller/follow_joint_trajectory'
        )

    def create_goal(self, side, angle):

        goal_msg = FollowJointTrajectory.Goal()

        if side == 'left':
            goal_msg.trajectory.joint_names = [
                'left_4C2_Joint1',
                'left_4C2_Joint2',
                'left_4C2_Joint3',
                'left_4C2_Joint4',
                'left_4C2_Joint5',
                'left_4C2_Joint6'
            ]

        elif side == 'right':
            goal_msg.trajectory.joint_names = [
                'right_4C2_Joint1',
                'right_4C2_Joint2',
                'right_4C2_Joint3',
                'right_4C2_Joint4',
                'right_4C2_Joint5',
                'right_4C2_Joint6'
            ]

        point = JointTrajectoryPoint()

        point.positions = [
            angle,
            angle,
            -angle,
            -angle,
            angle,
            angle
        ]

        point.time_from_start.sec = 3

        goal_msg.trajectory.points = [point]

        return goal_msg

    def send_goal(self, hand, angle):

        self.get_logger().info(
            f'hand={hand}, angle={angle:.3f}'
        )

        if hand in ['left', 'both']:

            self.left_action_client.wait_for_server()

            goal = self.create_goal(
                'left',
                angle
            )

            self.left_action_client.send_goal_async(
                goal
            )

        if hand in ['right', 'both']:

            self.right_action_client.wait_for_server()

            goal = self.create_goal(
                'right',
                angle
            )

            self.right_action_client.send_goal_async(
                goal
            )


def main(args=None):

    if len(sys.argv) != 3:

        print(
            "使い方:\n"
            "python3 gripper.py [left|right|both] [open|close]"
        )

        return

    hand = sys.argv[1]
    action = sys.argv[2]

    if hand not in ['left', 'right', 'both']:

        print(
            "hand は left / right / both"
        )

        return

    if action not in ['open', 'close']:

        print(
            "action は open / close"
        )

        return

    if action == 'open':
        angle = 47.0 * math.pi / 180.0
    else:
        angle = 3.0 * math.pi / 180.0

    rclpy.init()

    client = GripperClient()

    client.send_goal(
        hand,
        angle
    )

    rclpy.spin_once(
        client,
        timeout_sec=2.0
    )

    client.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()