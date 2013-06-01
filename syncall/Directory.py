class Directory:
    """
    Listens for file system changes in specific directory and applies
    changes from different sources.
    """
    def __init__(self, path):
        self.path = path
