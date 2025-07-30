import numpy as np
from typing import Dict, Tuple, List, Optional, Any, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from .metrics_calculator import MetricsCalculator

from .metrics_calculator import MetricsCalculator

class FeatureCoordinate:
    def __init__(self, mask: np.ndarray):
        """
        Initialize feature coordinate from mask
        Args:
            mask: Binary mask of the feature
        """
        if not isinstance(mask, np.ndarray):
            raise TypeError("Mask must be a numpy array")
        if mask.dtype != bool and mask.dtype != np.uint8:
            raise TypeError("Mask must be boolean or uint8")
            
        self.mask = mask.astype(bool)
        self.height, self.width = mask.shape
        self._compute_coordinates()

    def _compute_coordinates(self):
        """Compute bounding box and center point from mask"""
        y_indices, x_indices = np.nonzero(self.mask)
        
        if len(y_indices) == 0 or len(x_indices) == 0:
            self.bbox = None
            self.center = None
            self.area = 0
            return

        # Compute bounding box
        self.bbox = {
            'x1': int(np.min(x_indices)),
            'y1': int(np.min(y_indices)),
            'x2': int(np.max(x_indices)),
            'y2': int(np.max(y_indices))
        }

        # Compute center point
        self.center = {
            'x': int(np.mean(x_indices)),
            'y': int(np.mean(y_indices))
        }
        
        # Compute area
        self.area = int(np.sum(self.mask))

    @property
    def height(self) -> Optional[int]:
        """Get height of the feature"""
        if self.bbox:
            return self.bbox['y2'] - self.bbox['y1']
        return None

    @property
    def width(self) -> Optional[int]:
        """Get width of the feature"""
        if self.bbox:
            return self.bbox['x2'] - self.bbox['x1']
        return None

class FaceCoordinates:
    """Class for storing and accessing face feature coordinates"""
    
    # Complete feature map from model output indices to feature names
    FEATURE_MAP = {
        'background': 0,
        'skin': 1,
        'nose': 2,
        'left_eye': 3,
        'right_eye': 4,
        'left_eyebrow': 5,
        'right_eyebrow': 6,
        'left_ear': 7,
        'right_ear': 8,
        'mouth': 9,
        'upper_lip': 10,
        'lower_lip': 11,
        'hair': 12,
        'hat': 13,
        'eyeglasses': 14,
        'earrings': 15,
        'necklace': 16,
        'neck': 17,
        'clothes': 18
    }
    
    # Reverse mapping from indices to feature names
    INDEX_TO_FEATURE = {v: k for k, v in FEATURE_MAP.items()}
    
    def __init__(self, parsing_map: np.ndarray):
        """
        Initialize face coordinates from parsing map
        Args:
            parsing_map: 2D numpy array where each value corresponds to a feature index
        """
        if not isinstance(parsing_map, np.ndarray):
            raise TypeError("Parsing map must be a numpy array")
        if parsing_map.ndim != 2:
            raise ValueError("Parsing map must be 2-dimensional")
            
        self.parsing_map = parsing_map
        self.height, self.width = parsing_map.shape
        self._feature_coordinates = {}
        self._compute_all_coordinates()

    def _compute_all_coordinates(self):
        """Compute coordinates for all features in the parsing map"""
        for feature, index in self.FEATURE_MAP.items():
            mask = (self.parsing_map == index)
            if np.any(mask):
                self._feature_coordinates[feature] = FeatureCoordinate(mask)

    def get_feature_coordinates(self, feature: str) -> Optional[Dict[str, Any]]:
        """
        Get coordinates for a specific feature
        Args:
            feature: Name of the feature
        Returns:
            Dictionary with bbox, center, width, height if feature exists, None otherwise
        """
        if feature not in self.FEATURE_MAP:
            raise ValueError(f"Invalid feature name: {feature}. Valid features are: {list(self.FEATURE_MAP.keys())}")
            
        coord = self._feature_coordinates.get(feature)
        if coord is None:
            return None
            
        return {
            'bbox': coord.bbox,
            'center': coord.center,
            'width': coord.width,
            'height': coord.height,
            'area': coord.area
        }

    def get_feature_mask(self, feature: str) -> Optional[np.ndarray]:
        """
        Get binary mask for a specific feature
        Args:
            feature: Name of the feature
        Returns:
            Binary mask as numpy array if feature exists, None otherwise
        """
        if feature not in self.FEATURE_MAP:
            raise ValueError(f"Invalid feature name: {feature}")
            
        coord = self._feature_coordinates.get(feature)
        return coord.mask if coord else None

    def get_all_masks(self) -> Dict[str, np.ndarray]:
        """Get masks for all detected features"""
        return {feat: coord.mask 
                for feat, coord in self._feature_coordinates.items()}

    def get_metrics(self) -> Dict[str, Any]:
        """
        Calculate all metrics for the face
        Returns:
            Dictionary containing various facial measurements and metrics
        """
        calculator = MetricsCalculator(self.parsing_map, self)
        return calculator.calculate_all_metrics()
        
    def get_feature_embedding(self, feature: str) -> Optional[np.ndarray]:
        """
        Get the embedding vector for a specific feature
        Args:
            feature: Name of the feature
        Returns:
            numpy array containing the feature embedding
        """
        metrics = self.get_metrics()
        return metrics['feature_embeddings'].get(feature)

    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get embeddings for all detected features
        Returns:
            Dictionary mapping feature names to their embedding vectors
        """
        metrics = self.get_metrics()
        return metrics['feature_embeddings']

    def get_symmetry_score(self) -> float:
        """
        Get overall face symmetry score
        Returns:
            Float between 0 and 1, where 1 is perfectly symmetric
        """
        metrics = self.get_metrics()
        return metrics['symmetry_score']

    def get_relative_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get all metrics describing relative positions and proportions
        Returns:
            Dictionary of metric dictionaries
        """
        metrics = self.get_metrics()
        return {
            'aspect_ratios': metrics['aspect_ratios'],
            'relative_positions': metrics['relative_positions'],
            'normalized_distances': metrics['normalized_distances'],
            'feature_areas': metrics['feature_areas']
        }
