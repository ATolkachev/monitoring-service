import configparser

class ConfigReader:

    def __init__(self):
        self._config = configparser.ConfigParser()

    def load_defaults(self):
        Result = dict()
        Result['server'] = 'mongodb://127.0.0.1/'
        Result['database'] = 'monitoring'
        Result['address'] = '127.0.0.1'
        Result['port'] = 8080
        Result['forks'] = 4

        return Result

    def load_config(self, config = "./config.ini"):
        Result = self.load_defaults()

        if(self._config.read(config)==[]):
            print("There is no Config file")
        else:
            Result['server'] = self._config.get('db', 'server', fallback='mongodb://127.0.0.1/')
            Result['database'] = self._config.get('db', 'database', fallback='monitoring')
            Result['address'] = self._config.get('server', 'address', fallback='127.0.0.1')
            Result['port'] = self._config.get('server', 'port', fallback=8080)
            Result['forks'] = self._config.get('checker', 'forks', fallback=4)

        return Result

if __name__ == '__main__':
    print("Config parser for Monitor project")