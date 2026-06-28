#!/usr/bin/env python3
"""Reads webcam frames and publishes them to /camera/image_raw."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class WebcamPublisher(Node):
    def __init__(self):
        super().__init__('webcam_publisher')

        self.declare_parameter('device_id', 0)
        self.declare_parameter('fps', 30.0)

        device_id = self.get_parameter('device_id').value
        fps       = self.get_parameter('fps').value

        self.cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.get_logger().fatal(f'Cannot open camera device {device_id}')
            raise RuntimeError(f'Cannot open device {device_id}')

        w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.get_logger().info(f'Camera negotiated resolution: {int(w)}x{int(h)}')

        self.bridge      = CvBridge()
        self.pub         = self.create_publisher(Image, '/camera/image_raw', 10)
        self.timer       = self.create_timer(1.0 / fps, self._publish)
        self.frame_count = 0
        self.get_logger().info(f'Webcam publisher ready — device {device_id} @ {fps} fps')

    def _publish(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('Empty frame from camera (cap.read() returned False).')
            return
        self.frame_count += 1
        if self.frame_count % 30 == 1:
            self.get_logger().info(f'Captured frame #{self.frame_count}, shape={frame.shape}')
        msg              = self.bridge.cv2_to_imgmsg(frame, 'bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = WebcamPublisher()
        rclpy.spin(node)
    except RuntimeError as e:
        print(e)
    finally:
        if 'node' in dir() and rclpy.ok():
            node.destroy_node()
        rclpy.shutdown()
