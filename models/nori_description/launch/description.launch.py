"""Publish the NORI robot description and its joint transforms."""

import sys
from pathlib import Path

import yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    AndSubstitution,
    Command,
    FindExecutable,
    LaunchConfiguration,
    NotSubstitution,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


# Per-chassis USB serial paths, written by `nori-update-serial-ports`. Absent on
# a robot that has never been localized, in which case the committed defaults
# below apply and behaviour is exactly what it was before this file existed.
#
# Localization USED TO be applied by rewriting these tracked sources, which left
# every correctly commissioned robot with a dirty working tree -- and
# nori-update refuses to run against one, so commissioning by the book made a
# robot permanently un-updatable. See
# docs/decisions/0001-serial-port-localization-vs-ota.md.
#
# This is the CANONICAL copy of the helper.
# nori_moveit_config/launch/arms_moveit.launch.py and
# nori_bringup/launch/includes/lidar.launch.py carry the same one: all three
# packages are ament_cmake and so cannot share a Python module, and
# nori_cameras/launch/cameras.launch.py already resolves its own user config
# inline this way.
PORTS_CONFIG = Path("~/.config/nori/ports.yaml").expanduser()


def user_port(role):
    """Return the per-chassis path for `role`, or None to use the default.

    A missing file is the normal un-localized case and is silent. Anything
    else -- unreadable, unparseable, wrong shape -- warns rather than failing
    the launch, because the fallback still produces a robot that starts; the
    warning is what connects "wrong port" to this file when it does not.
    """
    try:
        document = yaml.safe_load(PORTS_CONFIG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, yaml.YAMLError) as error:
        print(f"warning: ignoring {PORTS_CONFIG}: {error}", file=sys.stderr)
        return None

    ports = (document or {}).get("ports")
    if not isinstance(ports, dict):
        print(
            f"warning: {PORTS_CONFIG} has no 'ports:' mapping; using defaults",
            file=sys.stderr,
        )
        return None

    value = ports.get(role)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        print(
            f"warning: {PORTS_CONFIG}: ports.{role} is not a device path",
            file=sys.stderr,
        )
        return None
    return value


def generate_launch_description():
    use_gui = LaunchConfiguration("use_gui")
    use_joint_state_publisher = LaunchConfiguration("use_joint_state_publisher")
    use_ros2_control = LaunchConfiguration("use_ros2_control")
    feetech_bus_port = LaunchConfiguration("feetech_bus_port")
    feetech_baud_rate = LaunchConfiguration("feetech_baud_rate")
    feetech_response_timeout_ms = LaunchConfiguration(
        "feetech_response_timeout_ms"
    )
    feetech_max_read_failures = LaunchConfiguration("feetech_max_read_failures")
    pico_port = LaunchConfiguration("pico_port")
    central_lift_calibration_file = LaunchConfiguration(
        "central_lift_calibration_file"
    )
    wheel_acceleration = LaunchConfiguration("wheel_acceleration")
    wheel_max_speed_raw = LaunchConfiguration("wheel_max_speed_raw")
    wheel_velocity_steps_per_raw = LaunchConfiguration(
        "wheel_velocity_steps_per_raw"
    )
    xacro_file = PathJoinSubstitution(
        [FindPackageShare("nori_description"), "urdf", "nori.urdf.xacro"]
    )

    robot_description = {
        "robot_description": ParameterValue(
            Command(
                [
                    FindExecutable(name="xacro"),
                    " ",
                    xacro_file,
                    " use_ros2_control:=",
                    use_ros2_control,
                    " feetech_bus_port:=",
                    feetech_bus_port,
                    " feetech_baud_rate:=",
                    feetech_baud_rate,
                    " feetech_response_timeout_ms:=",
                    feetech_response_timeout_ms,
                    " feetech_max_read_failures:=",
                    feetech_max_read_failures,
                    " pico_port:=",
                    pico_port,
                    " central_lift_calibration_file:=",
                    central_lift_calibration_file,
                    " wheel_acceleration:=",
                    wheel_acceleration,
                    " wheel_max_speed_raw:=",
                    wheel_max_speed_raw,
                    " wheel_velocity_steps_per_raw:=",
                    wheel_velocity_steps_per_raw,
                ]
            ),
            value_type=str,
        )
    }

    use_joint_state_publisher_gui = AndSubstitution(
        use_joint_state_publisher, use_gui
    )
    use_headless_joint_state_publisher = AndSubstitution(
        use_joint_state_publisher, NotSubstitution(use_gui)
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_gui",
                default_value="false",
                description="Use the joint-state publisher GUI.",
            ),
            DeclareLaunchArgument(
                "use_joint_state_publisher",
                default_value="true",
                description=(
                    "Publish placeholder movable-joint states. Disable this when "
                    "ros2_control's joint_state_broadcaster is running."
                ),
            ),
            DeclareLaunchArgument(
                "use_ros2_control",
                default_value="false",
                choices=["true", "false"],
                description=(
                    "Add the central-lift and wheel control systems. Use "
                    "nori_moveit_config for rotary-arm control."
                ),
            ),
            DeclareLaunchArgument(
                "feetech_bus_port",
                default_value=(
                    user_port("left_feetech")
                    or "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B79016521-if00"
                ),
                description="Serial device for the bus-1 wheels.",
            ),
            DeclareLaunchArgument(
                "feetech_baud_rate",
                default_value="1000000",
                description="Baud rate shared by the servos on bus 1.",
            ),
            DeclareLaunchArgument(
                "feetech_response_timeout_ms",
                default_value="12",
                description="Per-servo serial response timeout in milliseconds.",
            ),
            DeclareLaunchArgument(
                "feetech_max_read_failures",
                default_value="3",
                description="Consecutive failed reads before stopping the bus.",
            ),
            DeclareLaunchArgument(
                "pico_port",
                default_value=(
                    user_port("pico")
                    or "/dev/serial/by-id/usb-Raspberry_Pi_Pico_2_789ADB3F1073A144-if00"
                ),
                description="Persistent serial path for the central-lift Pico.",
            ),
            DeclareLaunchArgument(
                "central_lift_calibration_file",
                default_value="~/.config/nori/central_lift_calibration.yaml",
                description="Central-lift calibration audit record.",
            ),
            DeclareLaunchArgument(
                "wheel_acceleration",
                default_value="20",
                description="STS acceleration register value for both wheels.",
            ),
            DeclareLaunchArgument(
                "wheel_max_speed_raw",
                default_value="2200",
                description="Maximum wheel speed in STS encoder steps/second.",
            ),
            DeclareLaunchArgument(
                "wheel_velocity_steps_per_raw",
                default_value="1.0",
                description=(
                    "Encoder steps/second represented by one raw velocity unit."
                ),
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[robot_description],
                output="screen",
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                condition=IfCondition(use_joint_state_publisher_gui),
                output="screen",
            ),
            Node(
                package="joint_state_publisher",
                executable="joint_state_publisher",
                condition=IfCondition(use_headless_joint_state_publisher),
                output="screen",
            ),
        ]
    )
