import configparser


def main():
    config_test = ConfigHandler()
    config_test.generate_config_file()
    config_test.read_config_file()

class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()

    def generate_config_file(self):
        self.config.add_section('Settings')
        self.config.set('Settings', '# this is the comment for test1', '')
        self.config.set('Settings', 'test1', '1')
        self.config.set('Settings', '# This is the comment for test2', '')
        self.config.set('Settings', 'test2', '2')
        self.config.set('Settings', '# This Is The COmment For Test 3', 'blahhhhh')
        self.config.set('Settings', 'test3', '3')

        self.config['First Run Setting'] = {'recent_kill_id': ''}
        with open('Config.ini', 'w') as configfile:
            self.config.write(configfile)

    def read_config_file(self):
        with open('Config.ini', 'r') as config_file:
            file = self.config.read_file(config_file.read())
            print(file)


main()
