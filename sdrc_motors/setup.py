from setuptools import find_packages, setup

package_name = 'sdrc_motors'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pknadimp',
    maintainer_email='pknadimp@gmail.com',
    description='This package controls motors for a specific robotics application.',
    license='Apache 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_node = sdrc_motors.motor_node:main',
        ],
    },
)
