import toml
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path=Path('./config.toml')):
        self.config_path = config_path
        if self.config_path.exists():
            self.load()
        else:
            self.config = {
            "well_detector": {
                "dp": 1,
                "min_dist": 270, 
                "param1": 45,
                "param2": 20, 
                "min_radius": 120,
                "max_radius": 145,
                "eps": 350
            },
            "well_analyzer": {
                "hsv_lower_bound": (20, 18, 0),
                "hsv_upper_bound": (179, 255, 91)
            },
            "plate": {
                "grouping": True,
                "rows": 6,
                "cols": 4,
                "well_count": 24
            }
        }

    def validate(self):
        pass

    def load(self):
        with open(self.config_path, 'r') as f:
            self.config = toml.load(f)

    def update(self, data):
        self.config.update(data)
    
    def get(self, key):
        value = self.config.get(key)
        if not value:
            raise Exception(f'{key} not found in config {self.config_path}.')
        return value

    def write(self):
        with open(self.config_path, 'w') as f:
            toml.dump(self.config, f)

    def generate(self):
        if self.config_path.exists():
            raise Exception("File already exists.")
        self.write()