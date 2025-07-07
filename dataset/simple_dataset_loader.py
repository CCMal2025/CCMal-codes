import os


class SimpleDatasetLoader:
    def __init__(self, path):
        self.path = path
        self.file_list = os.listdir(self.path)

    def __iter__(self):
        for package_path in self.file_list:
            yield os.path.join(self.path, package_path)

    def __len__(self):
        return len(self.file_list)
