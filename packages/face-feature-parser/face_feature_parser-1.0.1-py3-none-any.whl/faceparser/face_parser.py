import os
import torch
import numpy as np
from PIL import Image
import cv2
import torchvision.transforms as transforms
from .model import BiSeNet

class FaceFeatureParser:
    # Face parsing class indices
    FEATURE_MAP = {
        'background': 0,
        'skin': 1,
        'nose': 2,
        'eyeglass': 3,
        'left_eye': 4,
        'right_eye': 5,
        'left_eyebrow': 6,
        'right_eyebrow': 7,
        'left_ear': 8,
        'right_ear': 9,
        'mouth': 10,
        'upper_lip': 11,
        'lower_lip': 12,
        'hair': 13,
        'hat': 14,
        'earring': 15,
        'necklace': 16,
        'neck': 17,
        'clothing': 18
    }

    def __init__(self, checkpoint_path, device=None):
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device

        self.net = BiSeNet(n_classes=19)
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
        
        self.net.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.net.to(self.device)
        self.net.eval()

        self.to_tensor = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])

    def parse_face(self, image_path, features=None):
        """
        Parse facial features from an image.
        Args:
            image_path (str): Path to the input image
            features (list, optional): List of specific features to extract. If None, all features are extracted.
        Returns:
            dict: Dictionary containing the parsing results and visualizations
        """
        img = Image.open(image_path)
        image = img.resize((512, 512), Image.BILINEAR)
        tensor_img = self.to_tensor(image)
        tensor_img = torch.unsqueeze(tensor_img, 0)
        tensor_img = tensor_img.to(self.device)

        with torch.no_grad():
            out = self.net(tensor_img)[0]
            parsing = out.squeeze(0).cpu().numpy().argmax(0)

        return self._process_features(image, parsing, features)

    def _process_features(self, image, parsing, features=None):
        """Process and visualize specific facial features."""
        if features is None:
            features = list(self.FEATURE_MAP.keys())

        results = {}
        for feature in features:
            if feature not in self.FEATURE_MAP:
                continue

            feature_idx = self.FEATURE_MAP[feature]
            mask = (parsing == feature_idx).astype(np.uint8) * 255
            
            # Create colored overlay
            colored_mask = np.zeros((parsing.shape[0], parsing.shape[1], 3), dtype=np.uint8)
            color = self._get_feature_color(feature)
            colored_mask[mask > 0] = color

            # Blend with original image
            image_np = np.array(image)
            blended = cv2.addWeighted(
                cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR),
                0.7,
                colored_mask,
                0.3,
                0
            )

            results[feature] = {
                'mask': mask,
                'visualization': blended
            }

        return results

    def _get_feature_color(self, feature):
        """Get color for feature visualization."""
        color_map = {
            'skin': [255, 224, 189],
            'nose': [255, 0, 0],
            'left_eye': [0, 255, 0],
            'right_eye': [0, 255, 0],
            'left_eyebrow': [0, 0, 255],
            'right_eyebrow': [0, 0, 255],
            'left_ear': [255, 255, 0],
            'right_ear': [255, 255, 0],
            'mouth': [255, 0, 255],
            'upper_lip': [255, 0, 128],
            'lower_lip': [255, 0, 128],
            'hair': [128, 0, 128],
            'hat': [128, 128, 0],
            'neck': [0, 128, 128],
            'clothing': [128, 128, 128]
        }
        return color_map.get(feature, [255, 255, 255])  # white for undefined features
