#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np
import math

def pca_orientation(contour):
    pts=contour.reshapre(-1,2).astype(np.float64)
    mean=np.mean(pts,axis=0)
    cov=np.cov((pts-mean).T)
    evals,evecs=np.linalg.eigh(cov)
    idx   = evals.argsort()[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]
    raw   = math.degrees(math.atan2(evecs[1, 0], evecs[0, 0]))
    angle = ((raw + 90.0) % 180.0) - 90.0
    return angle, mean, evecs, evals
def draw_annotation(frame, contour, angle, center, evecs, evals):
    cx, cy = int(center[0]), int(center[1])
    cv2.drawContours(frame, [contour], -1, (0, 255, 255), 2)
    rect = cv2.minAreaRect(contour)
    box  = cv2.boxPoints(rect)
    cv2.drawContours(frame, [np.intp(box)], -1, (255, 165, 0), 2)

    for col, color in enumerate([(0, 220, 0), (80, 80, 255)]):
        scale = math.sqrt(max(abs(evals[col]), 1.0)) * 0.5
        ex    = int(cx + evecs[0, col] * scale)
        ey    = int(cy + evecs[1, col] * scale)
        cv2.arrowedLine(frame, (cx, cy), (ex, ey), color, 2, tipLength=0.25)
    label = f'{angle:.1f} deg'
    font  = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(label, font, 0.6, 2)
    lx, ly = cx - tw // 2, cy - 18
    cv2.rectangle(frame, (lx - 4, ly - th - 2), (lx + tw + 4, ly + 4), (0, 0, 0), -1)
    cv2.putText(frame, label, (lx, ly), font, 0.6, (255, 255, 255), 2)
class OrientationDetectorNode(Node):
    def __init__(self):
        super().__init__('orientation_detector')
        self.declare_parameter('min_area',      1500)    # px² minimum contour area
        self.declare_parameter('max_area',      300000)  # px² maximum (avoids full-frame)
        self.declare_parameter('invert_thresh', False)   # True = light object on dark bg

        self.min_area = int(self.get_parameter('min_area').value)
        self.max_area = int(self.get_parameter('max_area').value)
        self.invert   = bool(self.get_parameter('invert_thresh').value)

        self.sub      = self.create_subscription(
            Image, '/camera/image_raw', self._callback, 10)
        self.vis_pub  = self.create_publisher(Image, '/orientation/image', 10)
        self.data_pub = self.create_publisher(
            Float64MultiArray, '/orientation/angles', 10)

        self.bridge = CvBridge()
        self.get_logger().info(
            f'Detector ready | area=[{self.min_area}, {self.max_area}] | '
            f'invert_thresh={self.invert}')
    def _preprocess(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)

        # Otsu automatically picks the best global threshold
        flag = (cv2.THRESH_BINARY     + cv2.THRESH_OTSU) if self.invert \
               else (cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _, mask = cv2.threshold(blur, 0, 255, flag)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
        return mask

    def _callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge error: {e}')
            return

        vis  = frame.copy()
        mask = self._preprocess(frame)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        angles = []
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if not (self.min_area < area < self.max_area):
                continue
            if len(cnt) < 5:  
                continue
            try:
                angle, center, evecs, evals = pca_orientation(cnt)
                angles.append(angle)
                draw_annotation(vis, cnt, angle, center, evecs, evals)
            except np.linalg.LinAlgError:
                continue 

        # Status overlay
        cv2.putText(vis, f'Objects detected: {len(angles)}',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 220, 0), 2)

        # Publish annotated image
        try:
            out        = self.bridge.cv2_to_imgmsg(vis, 'bgr8')
            out.header = msg.header
            self.vis_pub.publish(out)
        except Exception as e:
            self.get_logger().error(f'Image publish error: {e}')

        # Publish angle values as Float64 array
        data_msg      = Float64MultiArray()
        data_msg.data = [float(a) for a in angles]
        self.data_pub.publish(data_msg)


def main(args=None):
    rclpy.init(args=args)
    node = OrientationDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()