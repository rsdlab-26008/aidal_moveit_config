import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # ========== 1. パスとモデルの設定（Gazebo用） ==========
    desc_pkg_path = get_package_share_directory('aidal_description')
    rm_pkg_path = get_package_share_directory('rm_description')
    moveit_config_path = get_package_share_directory('aidal_moveit_config')
    
    # world_file_path = os.path.join(moveit_config_path, 'worlds', 'pick_and_place copy.world')
    #fix
    world_file_path = os.path.join(moveit_config_path, 'worlds', 'Task.world')

    install_dir_desc = os.path.dirname(os.path.dirname(desc_pkg_path))
    install_dir_rm = os.path.dirname(os.path.dirname(rm_pkg_path))
    install_dir_moveit = os.path.dirname(os.path.dirname(moveit_config_path))
    # gazebo_model_path = os.path.join(install_dir_desc, 'share') + ':' + os.path.join(install_dir_rm, 'share') + ':' + os.path.join(install_dir_moveit, 'share')
    #fix
    gazebo_model_path = os.path.join(install_dir_desc, 'share') + ':' + os.path.join(install_dir_rm, 'share') + ':' + os.path.join(install_dir_moveit, 'share') + ':' + os.path.join(moveit_config_path, 'models')

    set_gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=[gazebo_model_path, ':', os.environ.get('GAZEBO_MODEL_PATH', '')]
    )

    gazebo_plugin_path = os.path.join(install_dir_moveit, 'lib') + ':' + os.path.join(install_dir_desc, 'lib')
    set_gazebo_plugin_path = SetEnvironmentVariable(
        name='GAZEBO_PLUGIN_PATH',
        value=[gazebo_plugin_path, ':', os.environ.get('GAZEBO_PLUGIN_PATH', '')]
    )

    urdf_file_name = 'urdf/aidal_eg2-4c2.urdf'
    urdf = os.path.join(desc_pkg_path, urdf_file_name)

    with open(urdf, 'r') as infp:
        robot_description_str = infp.read()
    robot_description_str = robot_description_str.replace('$(find aidal_moveit_config)', moveit_config_path)

    # ========== 2. Gazeboとロボット状態の起動 ==========
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={'world': world_file_path, 'verbose': 'true'}.items()
    )

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_str, 'use_sim_time': True}])

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        #test
        # arguments=['-topic', 'robot_description', '-entity', 'RealMan_AIDAL', '-x', '0.35', '-y', '2.277', '-z', '0.005', '-Y', '1.5708'],
        # arguments=['-topic', 'robot_description', '-entity', 'RealMan_AIDAL', '-x', '1.5', '-y', '-2.5', '-z', '0.005', '-Y', '1.5708'],
        arguments=['-topic', 'robot_description', '-entity', 'RealMan_AIDAL', '-x', '0.7', '-y', '2.1', '-z', '0.005', '-Y', '1.5708'],
        output='screen')

    # コントローラーの起動設定
    controllers = [
        'joint_state_broadcaster',
        'diff_drive_controller',
        'left_arm_controller',
        'right_arm_controller',
        'left_gripper_controller',
        'right_gripper_controller',
        'lift_controller',
        'head_controller'
    ]
    
    load_controllers = []
    for ctrl in controllers:
        load_controllers.append(
            ExecuteProcess(
                cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', ctrl],
                output='screen'
            )
        )

    # ========== 3. MoveIt 2とRVizの起動 ==========
    moveit_config = MoveItConfigsBuilder("RealMan_AIDAL", package_name="aidal_moveit_config").to_moveit_configs()

    run_move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
                {"robot_description": robot_description_str},
                {"use_sim_time": True},
                {"default_planning_pipeline": "ompl"},
        ],
    )

    rviz_config_file = os.path.join(moveit_config_path, "config", "moveit.rviz")
    run_rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            
            # moveit_config.robot_description,
            # moveit_config.robot_description_semantic,
            # moveit_config.robot_description_kinematics,
            # {"use_sim_time": True},
            # {"default_planning_pipeline": "ompl"},

            {"robot_description": robot_description_str},
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": True},
            {"default_planning_pipeline": "ompl"},
        ],
    )

    # ========== 4. 全てのノードをリストにまとめて起動 ==========
    nodes_to_start = [
        set_gazebo_model_path,
        set_gazebo_plugin_path,
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        run_move_group_node,
        run_rviz_node
    ] + load_controllers

    return LaunchDescription(nodes_to_start)