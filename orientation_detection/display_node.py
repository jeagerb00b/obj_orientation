#!/usr/bin/env python3
"""
Subscribes to /orientation/image and renders it in a cv2 window.
Uses spin_once in a loop so cv2.imshow runs on the main thread — avoids
GUI freeze issues common with imshow inside subscriber callbacks.

Press  Q  in the window to quit.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class DisplayNode(Node):
    def __init__(self):
        super().__init__('display_node')
        self.bridge       = CvBridge()
        self.latest_frame = None
        self.sub = self.create_subscription(
            Image, '/orientation/image', self._callback, 10)
        self.get_logger().info('Display node ready — press Q in the window to quit.')

    def _callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(str(e))


def main(args=None):
    rclpy.init(args=args)
    node = DisplayNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.03)   # ~30 fps poll
            if node.latest_frame is not None:
                cv2.imshow('Object Orientation Detection', node.latest_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()