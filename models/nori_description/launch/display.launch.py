"""Run the description and RViz together for single-machine model work."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration("use_gui")
    use_rviz = LaunchConfiguration("use_rviz")
    launch_directory = PathJoinSubstitution(
        [FindPackageShare("nori_description"), "launch"]
    )

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([launch_directory, "description.launch.py"])
        ),
        launch_arguments={"use_gui": use_gui}.items(),
    )
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([launch_directory, "rviz.launch.py"])
        ),
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_gui",
                default_value="true",
                description="Start joint_state_publisher_gui instead of the non-GUI publisher.",
            ),
            DeclareLaunchArgument(
                "use_rviz",
                default_value="true",
                description="Start RViz with the NORI visualization configuration.",
            ),
            description_launch,
            rviz_launch,
        ]
    )
