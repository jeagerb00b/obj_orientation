#!/usr/bin/evn python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class WebcamPublisher(Node):
    def __init__(self):
        super().__init__('webcam_publisher')
        self.declare_parameter('device_id',0)
        self.declare_parameter('fps',30.0)
        
        device_id=self.get_parameter('device_id').value
        fps=self.get_parameter('fps').value
        self.cap=cv2.VideoCapture(device_id)
        if not self.cap.isOpened():
            self.get_logger().fatal(f'Cannot open camera device {device_id}')
            raise RuntimeError(f'Cannot open device {device_id}')

        self.bridge=CvBridge()
        self.pub=self.create_publisher(Image,'/webcam/image_raw',10)
        self.timer  = self.create_timer(1.0 / fps, self._publish)
        self.get_logger().info(f'Webcam publisher ready — device {device_id} @ {fps} fps')
    def _publish(self):
        ret, frame=self.cap.read()
        if not ret:
            self.get_logger().warn('Empty frame from camera.')
            return
        msg=self.bridge.cv2_to_imgmsg(frame, 'bgr8')
        msg.header.stamp=self.get_clock().now().to_msg()
        self.pub.publish(msg)
    def destroy_node(self):
        self.cap.release()
        return super().destroy_node()
def main(args=None):
    rclpy.init(args=args)
    try:
        node=WebcamPublisher()
        rclpy.spin(node)
    except RuntimeError as e:
        print(e)
    finally:
        if 'node' in dir() and rclpy.ok():
            node.destroy_node()
        rclpy.shutdown()