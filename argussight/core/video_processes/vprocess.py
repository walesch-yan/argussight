class Vprocess:
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        pass

class Test(Vprocess):
    def __init__(self) -> None:
        super().__init__()
    
    def run(self) -> None:
        print("Test succeeded")