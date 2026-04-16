import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from face_control.controller import FaceController

try:
    controller = FaceController()
    controller.run()
except KeyboardInterrupt:
    print("\nInterrupted by user.")
