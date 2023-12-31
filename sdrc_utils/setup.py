from setuptools import find_packages, setup

package_name = 'sdrc_utils'

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
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'decoder_node = sdrc_utils.decoder_node:main',
            'gps_follower_node = sdrc_utils.gps_follower_node:main'
        ],
    },
)
