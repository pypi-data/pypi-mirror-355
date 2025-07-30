import importlib.resources
import shutil

def extract_notebook(destination_path):
    with importlib.resources.path("chislaki.notebooks", "числаки_экз.ipynb") as path:
        shutil.copy(path, destination_path)
