try:
    import threading
    import os
    import sys
    import inspect
    from time import sleep
finally:
    currentdir = os.path.dirname(os.path.abspath(__file__))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir)
    from smdb_web_interface import WebCLIServer, Settings, UserCommand
    parentdir = os.path.dirname(parentdir)
    sys.path.insert(0, parentdir)


class MockClass:
    def __init__(self):
        self.cli = WebCLIServer(Settings(), self.mock_backend)

    def start_cli(self):
        self.cli.start()

    def stop_cli(self):
        self.cli.stop()

    def logger(self):
        sleep(30)
        self.cli.push_data(["Multi line command\nTesting line formatting", "And is a list"])

    def mock_backend(self, input: UserCommand) -> None:
        if (input.command == "start"):
            threading.Thread(target=self.logger).start()
        sleep(1)
        self.cli.push_data("Answer 1", input)
        sleep(1)
        self.cli.push_data("Answer 2", input)
        sleep(1)
        self.cli.push_data("Answer 3", input)


if __name__ == "__main__":
    mock = MockClass()
    mock.start_cli()
    print("Server started")
    mock.logger()    
    input("press return to exit")
    mock.stop_cli()
