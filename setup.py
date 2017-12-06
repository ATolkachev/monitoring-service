from setuptools import setup, find_packages
setup(
    name="monitor",
    version="0.1.1",
    packages=find_packages(),
    zip_safe=True,
    entry_points = {
        'console_scripts': [
        	'monitor-rest=monitor.rest:RunRest',        # сервис с REST интерфейсом
        	'monitor-checker=monitor.checker:RunChecker'   # сервис который осуществляет проверки
        ],
    }
)