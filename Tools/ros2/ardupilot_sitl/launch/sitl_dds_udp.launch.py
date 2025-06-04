# Copyright 2023 ArduPilot.org.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Launch ArduPilot SITL, MAVProxy and the microROS DDS agent.

Run with default arguments:

ros2 launch ardupilot_sitl sitl_dds_udp.launch.py
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo, IncludeLaunchDescription, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch import LaunchContext
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PythonExpression


#def generate_launch_arguments():
#    DeclareLaunchArgument(
#        "instance",
#        default_value="0",
#        description="Instance number for multiple SITL instances (0, 1, 2, ...)"
#    ),
    #DeclareLaunchArgument(
    #    "transport",
    #    default_value="udp4",
    #    description="Transport protocol for micro-ROS agent (e.g., udp4, serial, etc.)"
    #),
    #DeclareLaunchArgument(
    #    "port",
    #    default_value="2019",   # Port for micro-ROS agent
    #    description="Port for micro-ROS agent"
    #),
    #DeclareLaunchArgument(
    #    "synthetic_clock",
    #    default_value="True",
    #    description="Use synthetic clock for simulation time"
    #),
    #DeclareLaunchArgument(
    #    "wipe",
    #    default_value="False",
    #    description="Wipe the SITL state before starting"
    #),
    #DeclareLaunchArgument(
    #    "model",
    #    default_value="quad",
    #    description="SITL model type (e.g., quad, plane, rover)"
    #),
    #DeclareLaunchArgument(
    #    "speedup",
    #    default_value="1",
    #    description="Speedup factor for SITL simulation"
    #),
    #DeclareLaunchArgument(
    #    "slave",
    #    default_value="0",
    #    description="Slave instance number for multiple SITL instances"
    #),
    #DeclareLaunchArgument(
    #    "defaults",
    #    default_value=PathJoinSubstitution([
    #        FindPackageShare("ardupilot_sitl"),
    #        "defaults",
    #        "sitl_defaults.json"
    #    ]),
    #    description="Path to SITL defaults JSON file"
    #),
    #DeclareLaunchArgument(
    #    "sim_address",
    #    default_value="",
    #    description="Address for the simulation (e.g.",
    #)
    #DeclareLaunchArgument(
    #    "master",
    #    default_value="tcp:127.0.0.1:5760",
    #    description="MAVLink master URI for SITL"
    #),
    #DeclareLaunchArgument(
    #    "sitl",
    #    default_value="127.0.0.1:5501",
    #    description="SITL address for MAVProxy"
    #),
    #DeclareLaunchArgument(
    #    "micro_ros_agent_ns",
    #    default_value="micro_ros_agent",
    #    description="Namespace for the micro-ROS agent"
    #)

def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])

# def under_wsl2():
#     import platform
#     return 'microsoft-standard-WSL2' in platform.release()
# 
# 
# def wsl2_host_ip():
#     if not under_wsl2():
#         return None
# 
#     pipe = subprocess.Popen("ip route show default | awk '{print $3}'",
#                             shell=True,
#                             stdout=subprocess.PIPE)
#     output_lines = pipe.stdout.read().decode('utf-8').strip(' \r\n')
#     ret = pipe.wait()
# 
#     if ret != 0:
#         # Command exited with an error. The output it generated probably isn't what we're expecting
#         return None
# 
#     if not output_lines:
#         # No output detected, maybe there's no nameserver or WSL2 has some abnormal firewalls/network settings?
#         return None
# 
#     return str(output_lines)

def launch_setup(context, *args, **kwargs):
    transport = LaunchConfiguration("transport")
    port = LaunchConfiguration("port")
    command = LaunchConfiguration("command")
    synthetic_clock = LaunchConfiguration("synthetic_clock")
    wipe = LaunchConfiguration("wipe")
    model = LaunchConfiguration("model")
    speedup = LaunchConfiguration("speedup")
    slave = LaunchConfiguration("slave")
    defaults = LaunchConfiguration("defaults")
    sim_address = LaunchConfiguration("sim_address")
    master = LaunchConfiguration("master")
    sitl = LaunchConfiguration("sitl")
    instance_str = LaunchConfiguration("instance").perform(context)
    instance = int(instance_str)
    is_micro = LaunchConfiguration("is_micro").perform(context)

    # Now you can safely use instance like a normal int or string
    homes = {
        "0": "35.6895,139.6917,584,0",
        "1": "34.0522,-118.2437,89,0",
        "2": "51.5074,-0.1278,15,0"
    }
    home = homes.get(instance_str, "0,0,0,0")

    transport = LaunchConfiguration("transport").perform(context)
    port = LaunchConfiguration("port").perform(context)

    # returns a valid IP of the host windows computer if we're WSL2.
    # This is run before the loop so it only runs once
    # wsl2_host_ip_str = wsl2_host_ip()

    micro_ros_ns = f"agent_{instance}"
    agent_port = str(int(port) + (instance * 10))
    sitl_port = str(5501 + (instance * 10))
    master_port = str(5760 + (instance * 10))

    sitl_address = f"127.0.0.1:{sitl_port}"
    master_uri = f"tcp:127.0.0.1:{master_port}"
    mavproxy_out = f"127.0.0.1:{14550 + (instance * 10)}"

    if is_micro == "True":
        micro_ros_agent = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare("ardupilot_sitl"),
                    "launch",
                    "micro_ros_agent.launch.py",
                ])
            ]),
            launch_arguments={
                "micro_ros_agent_ns": micro_ros_ns,
                "transport": transport,
                "port": "2019",
                "ref": "~/rdu_ws/src/ardupilot/libraries/AP_DDS/dds_xrce_profile.xml"
            }.items(),
        )

    sitl = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("ardupilot_sitl"),
                "launch",
                "sitl.launch.py",
            ])
        ]),
        launch_arguments={
            "instance": instance_str,
            "command": command,
            "model": model,
            "home": "-35.363262,149.165237,584.0,0", # Should be the same for all vehicle instances
            "defaults": defaults,
            "sim_address": sim_address,
            "master": master,
            "sitl": sitl_address,
            "transport": transport,
            "port": agent_port,
            "slave": slave,
            "speedup": "1",
            "wipe": "True",
            "synthetic_clock": "True",
        }.items()
    )

    mavproxy = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("ardupilot_sitl"),
                "launch",
                "mavproxy.launch.py",
            ])
        ]),
        launch_arguments={
            "master": master_uri,
            "sitl": sitl_address,
            "out": mavproxy_out,
            "console": "False",
            "map": "False",
        }.items()
    )

    if is_micro == "True":
        return [micro_ros_agent, sitl, mavproxy]
    else:
        return [sitl, mavproxy]
