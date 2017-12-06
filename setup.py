from setuptools import setup, find_packages
setup(
    name="MonitorService",
    version="0.1",
    packages=find_packages(),
    scripts=['monitor.rest.py','monitor.checker.py'],
    zip_safe=True,
    entry_points = {
        'console_scripts': [
        	'monitor-rest=monitor.rest:main',        # сервис с REST интерфейсом
        	'monitor-checker=monitor.checker:main'   # сервис который осуществляет проверки
        ],
    }
)