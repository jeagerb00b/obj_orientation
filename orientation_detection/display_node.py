#!/usr/bin/env python3
"""
Subscribes to /orientation/image and renders it in a cv2 window.

Hardened version:
  - forces the xcb (XWayland) Qt platform plugin explicitly, avoiding
    native-Wayland window creation issues common on GNOME
  - shows a self-test frame immediately on startup, BEFORE any camera
    data arrives, to isolate window-visibility issues from data-flow issues
  - throttled frame-count logging so silent stalls are visible in the logs
  - defensive try/except around every imshow call

Press  Q  in the window to quit.
"""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

WINDOW_NAME = 'Object Orientation Detection'


class DisplayNode(Node):
    def __init__(self):
        super().__init__('display_node')
        self.bridge       = CvBridge()
        self.latest_frame = None
        self.frame_count  = 0
        self.sub = self.create_subscription(
            Image, '/orientation/image', self._callback, 10)
        self.get_logger().info('Display node ready — press Q in the window to quit.')

    def _callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.frame_count += 1
            if self.frame_count % 30 == 1:
                self.get_logger().info(
                    f'Display received frame #{self.frame_count}, shape={self.latest_frame.shape}')
        except Exception as e:
            self.get_logger().error(f'imgmsg_to_cv2 failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = DisplayNode()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 640, 480)
    cv2.moveWindow(WINDOW_NAME, 100, 100)

    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_frame, 'Waiting for camera frames...', (40, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.imshow(WINDOW_NAME, test_frame)
    cv2.waitKey(1)
    node.get_logger().info('Self-test frame shown.')

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.03)
            if node.latest_frame is not None:
                try:
                    cv2.imshow(WINDOW_NAME, node.latest_frame)
                except Exception as e:
                    node.get_logger().error(f'imshow failed: {e}')
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()
