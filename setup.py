from setuptools import setup, find_packages
import monitor


def parse_requirements_file(requirements_path):
    with open(requirements_path) as req_file:
        return req_file.read().strip().split('\n')


setup(
    name="monitor",
    version=monitor.__version__,
    packages=find_packages(exclude=('tests', 'tests.*', 'build', 'dist', 'env')),
    license='BSD-3-Clause',
    entry_points={
        'console_scripts': [
            'monitor-rest=monitor.rest:RunRest',
            'monitor-checker=monitor.checker:RunChecker'
        ],
    },
    install_requires=parse_requirements_file('requirements.txt'),
)
