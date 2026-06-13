from setuptools import find_packages, setup
import os
from glob import glob
package_name = 'orientation_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jeagerboob',
    maintainer_email='sarfarasyoonas@gmail.com',
    description='Object orientation detection using PCA and OpenCV in ROS 2 Humble',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'webcam_publisher = orientation_detection.webcam_publisher:main',
            'orientation_detector = orientation_detection.orientation_node:main',
            'display_node = orientation_detection.display_node:main',
        ],
    },
)
