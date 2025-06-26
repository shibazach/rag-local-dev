# sitecustomize.py  (ルート直下に配置)
import os, sys
ROOT_DIR = os.path.dirname(__file__)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
