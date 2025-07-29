from .all_name import get_name_usages
from .invalid_name import _is_illegal_name
import os
import codecs
from typing import List
import __main__

def detect_file_encodings(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No such a file: {file_path}")
    
    common_encodings = [
        'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be',
        'utf-32', 'utf-32-le', 'utf-32-be',
        'ascii', 'latin1', 'iso-8859-1',
        'gbk', 'gb18030', 'big5',
        'shift_jis', 'euc-jp',
        'cp1251', 'cp1252', 'cp1250',
    ]
    
    successful_encodings = []
    
    for encoding in common_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            successful_encodings.append(encoding)
        except Exception as e:
            continue
    
    if not successful_encodings:
        return []
    else:
        return successful_encodings
    
if hasattr(__main__, "__file__"):
    all_name = set()
    for i in detect_file_encodings(__main__.__file__):
        with open(__main__.__file__) as f:
            try:
                analyse = get_name_usages(f.read())
                all_name |= set(analyse[0]) | set(analyse[1])
            except Exception:
                pass
    for i in all_name:
        if _is_illegal_name(i):
            raise NameError(f"name '{i}' is illegal. Please don't try to define a female.")
