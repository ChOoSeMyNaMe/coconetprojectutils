import os
from typing import List


def get_files(dir: str, extension: str = None) -> List[str]:
    result = []
    files = os.listdir(dir)
    for file in files:
        if os.path.isfile(file) and (extension is None or file.endswith("." + extension)):
            result.append(os.path.join(dir, file))
    return result
