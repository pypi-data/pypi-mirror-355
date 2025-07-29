import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from imblearn.over_sampling import RandomOverSampler
from brainflow import BoardShim
from application.classifier import Classifier


class ClassifierTest(unittest.TestCase):
    @patch('neuroengine.classifier.models', {'SVM': SVC(kernel='linear', C=1, probability=True, random_state=32),
                                             'LDA': LinearDiscriminantAnalysis()})
    @patch('neuroengine.classifier.layouts', {1: {"channels": [1, 2, 3], "eeg_start": 0, "eeg_end": 3}})
    def setUp(self):
        self.classifier = Classifier('SVM', 1)

    @patch('neuroengine.classifier.convert_to_mne')
    @patch('neuroengine.classifier.basic_preprocessing_pipeline')
    @patch('neuroengine.classifier.extract_epochs')
    def test_preprocess(self, mock_convert_to_mne, mock_basic_preprocessing_pipeline, mock_extract_epochs):
        data = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        self.classifier.preprocess(data)
        mock_convert_to_mne.assert_called_once()
        mock_basic_preprocessing_pipeline.assert_called_once()
        mock_extract_epochs.assert_called_once()

    @patch('neuroengine.classifier.RandomOverSampler.fit_resample')
    def test_train_with_oversampling(self, mock_fit_resample):
        data = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        self.classifier.train(data, oversample=True)
        mock_fit_resample.assert_called_once()

    @patch('neuroengine.classifier.RandomOverSampler.fit_resample')
    def test_train_without_oversampling(self, mock_fit_resample):
        data = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        self.classifier.train(data, oversample=False)
        mock_fit_resample.assert_not_called()

    @patch('neuroengine.classifier.SVC.predict')
    def test_predict(self, mock_predict):
        data = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        self.classifier.predict(data)
        mock_predict.assert_called_once()


if __name__ == '__main__':
    unittest.main()
