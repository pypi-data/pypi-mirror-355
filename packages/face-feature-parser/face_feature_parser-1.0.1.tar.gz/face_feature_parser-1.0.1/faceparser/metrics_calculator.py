import numpy as np
from typing import Dict, List, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .coordinates import FaceCoordinates

class MetricsCalculator:
    def __init__(self, parsing_map: np.ndarray, coordinates: 'FaceCoordinates'):
        """
        Initialize metrics calculator
        Args:
            parsing_map: 2D numpy array of feature classifications
            coordinates: FaceCoordinates object with feature locations
        """
        self.parsing_map = parsing_map
        self.coordinates = coordinates
        self.image_height, self.image_width = parsing_map.shape

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all face metrics"""
        return {
            'symmetry_score': self.calculate_symmetry_score(),
            'aspect_ratios': self.calculate_aspect_ratios(),
            'feature_areas': self.calculate_feature_areas(),
            'relative_positions': self.calculate_relative_positions(),
            'normalized_distances': self.calculate_normalized_distances(),
            'feature_embeddings': self.calculate_feature_embeddings()
        }

    def calculate_symmetry_score(self) -> float:
        """Calculate face symmetry score"""
        # Get key paired features
        paired_features = [
            ('left_eye', 'right_eye'),
            ('left_eyebrow', 'right_eyebrow'),
            ('left_ear', 'right_ear')
        ]

        symmetry_scores = []
        face_center = self.image_width // 2

        for left_feat, right_feat in paired_features:
            left_coords = self.coordinates.get_feature_coordinates(left_feat)
            right_coords = self.coordinates.get_feature_coordinates(right_feat)

            if left_coords and right_coords and left_coords.get('center') and right_coords.get('center'):
                # Calculate distance from face center
                left_dist = abs(left_coords['center']['x'] - face_center)
                right_dist = abs(right_coords['center']['x'] - face_center)
                
                # Calculate vertical alignment
                vert_diff = abs(left_coords['center']['y'] - right_coords['center']['y'])
                
                # Calculate size similarity
                size_ratio = min(left_coords['width'] / max(1, right_coords['width']),
                               right_coords['width'] / max(1, left_coords['width']))
                
                # Combine metrics
                pair_symmetry = (
                    (1 - abs(left_dist - right_dist) / self.image_width) * 0.4 +
                    (1 - vert_diff / self.image_height) * 0.4 +
                    size_ratio * 0.2
                )
                symmetry_scores.append(pair_symmetry)

        return float(np.mean(symmetry_scores)) if symmetry_scores else 0.0

    def calculate_aspect_ratios(self) -> Dict[str, float]:
        """Calculate aspect ratios for all features"""
        aspect_ratios = {}
        for feature in self.coordinates.FEATURE_MAP.keys():
            coords = self.coordinates.get_feature_coordinates(feature)
            if coords and coords.get('width') and coords.get('height') and coords['height'] > 0:
                aspect_ratios[feature] = coords['width'] / coords['height']
        return aspect_ratios

    def calculate_feature_areas(self) -> Dict[str, float]:
        """Calculate normalized areas for all features"""
        total_pixels = float(self.image_width * self.image_height)
        feature_areas = {}
        
        for feature, class_id in self.coordinates.FEATURE_MAP.items():
            feature_mask = (self.parsing_map == class_id)
            area = np.sum(feature_mask) / total_pixels
            feature_areas[feature] = float(area)
            
        return feature_areas

    def calculate_normalized_distances(self) -> Dict[str, float]:
        """Calculate normalized distances between feature pairs"""
        distances = {}
        face_diagonal = np.sqrt(self.image_width**2 + self.image_height**2)
        
        feature_pairs = [
            ('left_eye', 'right_eye', 'eye_separation'),
            ('nose', 'mouth', 'nose_to_mouth'),
            ('left_eye', 'nose', 'left_eye_to_nose'),
            ('right_eye', 'nose', 'right_eye_to_nose'),
            ('left_eyebrow', 'left_eye', 'left_brow_to_eye'),
            ('right_eyebrow', 'right_eye', 'right_brow_to_eye')
        ]

        for feat1, feat2, name in feature_pairs:
            coord1 = self.coordinates.get_feature_coordinates(feat1)
            coord2 = self.coordinates.get_feature_coordinates(feat2)
            
            if coord1 and coord2 and coord1.get('center') and coord2.get('center'):
                dist = np.sqrt(
                    (coord1['center']['x'] - coord2['center']['x'])**2 +
                    (coord1['center']['y'] - coord2['center']['y'])**2
                )
                distances[name] = float(dist / face_diagonal)

        return distances

    def calculate_relative_positions(self) -> Dict[str, float]:
        """Calculate relative positions of features"""
        positions = {}
        
        # Get face bounds from skin
        skin = self.coordinates.get_feature_coordinates('skin')
        if not skin or not skin.get('bbox'):
            return positions

        face_height = max(1, skin['height'])
        face_width = max(1, skin['width'])
        face_top = skin['bbox']['y1']
        face_left = skin['bbox']['x1']

        # Calculate normalized positions for each feature
        for feature in self.coordinates.FEATURE_MAP.keys():
            coords = self.coordinates.get_feature_coordinates(feature)
            if coords and coords.get('center'):
                positions[f"{feature}_x"] = float((coords['center']['x'] - face_left) / face_width)
                positions[f"{feature}_y"] = float((coords['center']['y'] - face_top) / face_height)

        return positions

    def calculate_feature_embeddings(self) -> Dict[str, np.ndarray]:
        """Calculate feature embeddings for deep learning"""
        embeddings = {}
        
        for feature in self.coordinates.FEATURE_MAP.keys():
            coords = self.coordinates.get_feature_coordinates(feature)
            if not coords or not coords.get('bbox'):
                continue

            # Create feature embedding vector: [x, y, width, height, area, aspect_ratio]
            embedding = np.array([
                coords['center']['x'] / self.image_width,  # normalized x center
                coords['center']['y'] / self.image_height,  # normalized y center
                coords['width'] / self.image_width,  # normalized width
                coords['height'] / self.image_height,  # normalized height
                (coords['width'] * coords['height']) / (self.image_width * self.image_height),  # normalized area
                coords['width'] / max(1, coords['height'])  # aspect ratio
            ], dtype=np.float32)
            
            embeddings[feature] = embedding

        return embeddings
