class Directory:
    """
    Listens for file system changes in specific directory and applies
    changes from different sources.
    """
    def __init__(self, path, index_name='.syncall_index'):
        self.path = path
        self.index_file_name = index_name

    def load_index(self):
        pass
