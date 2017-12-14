from setuptools import setup, find_packages
import monitor

setup(
    name="monitor",
    version=monitor.__version__,
    packages=find_packages(),
    scripts=['monitor/rest.py', 'monitor/checker.py', 'monitor/config.py'],
    zip_safe=True,
    license='BSD-3-Clause',
    entry_points={
        'console_scripts': [
            'monitor-rest=monitor.rest:RunRest',  # сервис с REST интерфейсом
            'monitor-checker=monitor.checker:RunChecker'  # сервис который осуществляет проверки
        ],
    },
    install_requires=["asyncio", "aiohttp", "pymongo", "pika"],
)
