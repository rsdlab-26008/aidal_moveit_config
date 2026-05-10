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
        # 左右のグリッパーのコントローラに接続
        self.left_action_client = ActionClient(self, FollowJointTrajectory, '/left_gripper_controller/follow_joint_trajectory')
        self.right_action_client = ActionClient(self, FollowJointTrajectory, '/right_gripper_controller/follow_joint_trajectory')

    def send_goal(self, angle):
        left_goal_msg = FollowJointTrajectory.Goal()
        left_goal_msg.trajectory.joint_names = [
            'left_4C2_Joint1', 'left_4C2_Joint2', 'left_4C2_Joint3',
            'left_4C2_Joint4', 'left_4C2_Joint5', 'left_4C2_Joint6'
        ]
        
        right_goal_msg = FollowJointTrajectory.Goal()
        right_goal_msg.trajectory.joint_names = [
            'right_4C2_Joint1', 'right_4C2_Joint2', 'right_4C2_Joint3',
            'right_4C2_Joint4', 'right_4C2_Joint5', 'right_4C2_Joint6'
        ]
        
        point = JointTrajectoryPoint()
        point.positions = [angle, angle, -angle, -angle, angle, angle]
        point.time_from_start.sec = 3  # 3秒かけて動かす
        
        left_goal_msg.trajectory.points = [point]
        right_goal_msg.trajectory.points = [point]

        self.get_logger().info(f"angle:{angle:.3f}")
        self.left_action_client.wait_for_server()
        self.right_action_client.wait_for_server()
        
        self.left_action_client.send_goal_async(left_goal_msg)
        self.right_action_client.send_goal_async(right_goal_msg)

def main(args=None):
    if len(sys.argv) < 2 or sys.argv[1] not in ['open', 'close']:
        print("使い方: python3 gripper.py [open|close]")
        return

    angle = 47.0 * math.pi / 180.0 if sys.argv[1] == 'open' else 15 * math.pi / 180.0

    rclpy.init()
    client = GripperClient()
    
    client.send_goal(angle) 
    
    rclpy.spin_once(client, timeout_sec=2.0)
    client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
