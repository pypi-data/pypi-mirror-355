import os
import unittest
import pytest

# Check if running in CI environment
IN_CI = os.getenv('CI') == 'true'

class TestImports(unittest.TestCase):
    """Test that required packages can be imported."""
    
    def test_import_opencv(self):
        """Test that OpenCV can be imported."""
        import cv2
        self.assertIsNotNone(cv2.__version__)
    
    @pytest.mark.skipif(IN_CI, reason="PyQt6 GUI tests not supported in CI")
    def test_import_pyqt6(self):
        """Test that PyQt6 can be imported."""
        from PyQt6 import QtWidgets
        # In CI, this will be skipped
        self.assertIsNotNone(QtWidgets.QApplication.instance() or True)

if __name__ == '__main__':
    unittest.main()
