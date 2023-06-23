import os


class Shell:


    def execute(self, command : str) -> list:
        stream = os.popen(command)
        output = stream.read().split('\n')
        return list(filter(None, output))

