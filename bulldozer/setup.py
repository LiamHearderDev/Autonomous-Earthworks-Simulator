import os
from glob import glob
from setuptools import setup

package_name = 'bulldozer'

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
        
        # For ROS2 model configurations
        (os.path.join('share', package_name, 'model'),
            glob('model/*')),

        # Gazebo worlds
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.sdf')),

        # Meshes, if your URDF references any (STL/DAE etc.)
        (os.path.join('share', package_name, 'meshes'),
            glob('meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='liamhearder',
    maintainer_email='LiamHearderDev@gmail.com',
    description='ROS 2 and Gazebo movement scaffold for an autonomous bulldozer.',
    license='TODO: License declarations?',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'bulldozer_teleop = bulldozer.bulldozer_teleop:main',
        ],
    },
)
