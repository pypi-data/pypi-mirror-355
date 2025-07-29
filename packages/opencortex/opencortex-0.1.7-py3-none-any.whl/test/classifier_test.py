
# Unit tests for the Classifier class

import unittest

from application.classifier import Classifier


class TestClassifier(unittest.TestCase):

    # Test if the model is None
    def test_model_none(self):
        with self.assertRaises(ValueError):
            Classifier(None, 0)

    # Test if the model is not None
    def test_model_not_none(self):
        model = Classifier('LDA', 0)
        self.assertIsNotNone(model.model)

    # Test if the board_id is None
    def test_board_id_none(self):
        with self.assertRaises(ValueError):
            Classifier('LDA', None)

    # Test if the board_id is not None
    def test_board_id_not_none(self):
        model = Classifier('LDA', 0)
        self.assertIsNotNone(model.board_id)

    # Test if the sampling rate is not None
    def test_fs_not_none(self):
        model = Classifier('LDA', 0)
        self.assertIsNotNone(model.fs)

    # Test if the channels are not None
    def test_chs_not_none(self):
        model = Classifier('LDA', 0)
        self.assertIsNotNone(model.chs)

