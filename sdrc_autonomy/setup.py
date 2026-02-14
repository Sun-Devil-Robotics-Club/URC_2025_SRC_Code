from setuptools import setup, find_packages

package_name = 'sdrc_autonomy'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(include=[package_name, package_name + '.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'utm', 'opencv-python'],
    zip_safe=True,
    maintainer='lorenzoam',
    maintainer_email='lamart66@asu.edu',
    description='Autonomy package for SDRC rover',
    license='Apache 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'bt_runner = sdrc_autonomy.bt_runner:main',
            'autonomy_node = sdrc_autonomy.autonomy_node:main',
            'detect_ar_tag = sdrc_autonomy.actions.detect_ar_tag:main',
            'detect_object = sdrc_autonomy.actions.detect_object:main',
            'semantic_localizer = sdrc_autonomy.actions.semantic_localizer:main',
        ],
    },
)
