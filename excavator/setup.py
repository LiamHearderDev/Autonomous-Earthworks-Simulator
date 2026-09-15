import os
from glob import glob
from setuptools import setup

package_name = 'excavator'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        # Required by every ament_python package
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        (os.path.join('share', package_name), ['package.xml']),

        # Launch files
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),

        # URDF / xacro files
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')),

        # Bridge / other config files
        (os.path.join('share', package_name, 'config'),
            glob('config/*')),

        # Meshes, if your URDF references any (STL/DAE etc.)
        (os.path.join('share', package_name, 'meshes'),
            glob('meshes/*')),

        # For ROS2 model configurations
        (os.path.join('share', package_name, 'model'),
            glob('model/*')),

        # For world files
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='liamhearder',
    maintainer_email='LiamHearderDev@gmail.com',
    description='TODO: excavator package description',
    license='TODO: License declarations?',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Add here any Python nodes you write
            'arm_teleop = excavator.arm_teleop:main',
            'excavator_teleop = excavator.excavator_teleop:main',
        ],
    },
)