from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package='orientation_detection',
            executable='webcam_publisher',
            name='webcam_publisher',
            parameters=[{
                'device_id': 0,      # change to 2 or 4 if /dev/video0 doesn't work
                'fps':       30.0,
            }],
        ),

        Node(
            package='orientation_detection',
            executable='orientation_detector',
            name='orientation_detector',
            parameters=[{
                'min_area':      1500,    # increase if noise is detected
                'max_area':      300000,  # decrease if full background is detected
                'invert_thresh': False,   # set True for light object on dark background
            }],
        ),

        Node(
            package='orientation_detection',
            executable='display_node',
            name='display_node',
        ),
    ])