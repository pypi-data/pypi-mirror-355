import os
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from .bisenet import BiSeNet
from .coordinates import FaceCoordinates
from pathlib import Path

class FaceParser:
    DEFAULT_MODEL_PATH = os.path.expanduser('~/.faceparser/models/79999_iter.pth')
    
    def __init__(self, checkpoint_path: str = None):
        """
        Initialize the FaceParser model
        Args:
            checkpoint_path: Path to the model checkpoint. If None, will try to load from default locations.
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize model
        self.net = BiSeNet(n_classes=19)
        
        # Try to load checkpoint from various locations
        if checkpoint_path is None:
            checkpoint_paths = [
                self.DEFAULT_MODEL_PATH,  # User's home directory
                '79999_iter.pth',  # Current directory
                os.path.join(os.path.dirname(__file__), '79999_iter.pth'),  # Package directory
                os.path.join(os.path.dirname(os.path.dirname(__file__)), '79999_iter.pth')  # Parent directory
            ]
            
            for path in checkpoint_paths:
                if os.path.exists(path):
                    checkpoint_path = path
                    break
        
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(
                "Model checkpoint not found. Please either:\n"
                "1. Run 'faceparser install' to download the model\n"
                "2. Provide the path to an existing checkpoint\n"
                f"Tried locations: {', '.join(checkpoint_paths)}"
            )
        
        print(f"Loading checkpoint from: {checkpoint_path}")
        
        try:
            state_dict = torch.load(checkpoint_path, map_location=self.device)
        except Exception as e:
            raise RuntimeError(f"Failed to load checkpoint: {str(e)}")

        # Clean up state dict keys
        new_state_dict = {}
        for k, v in state_dict.items():
            # Remove 'module.' and 'cp.' prefixes if present
            new_key = k.replace('module.', '').replace('cp.', '')
            new_state_dict[new_key] = v

        # Load the modified state dict
        try:
            self.net.load_state_dict(new_state_dict, strict=False)
        except Exception as e:
            print(f"Warning: Some keys could not be loaded: {str(e)}")
        
        self.net.to(self.device)
        self.net.eval()
        
        # Set up image transforms
        self.to_tensor = transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225])
        ])

    def parse(self, image_path: str) -> tuple:
        """
        Parse face features from image
        Returns:
            tuple: (parsing_map, coordinates)
            - parsing_map: numpy array with feature class IDs
            - coordinates: FaceCoordinates object with feature locations
        """
        # Load and preprocess image
        img = Image.open(image_path)
        image = img.resize((512, 512), Image.BILINEAR)
        img_tensor = self.to_tensor(image)
        img_tensor = torch.unsqueeze(img_tensor, 0)
        img_tensor = img_tensor.to(self.device)

        # Get parsing map
        with torch.no_grad():
            out = self.net(img_tensor)[0]
            parsing = out.squeeze(0).cpu().numpy().argmax(0)

        # Create coordinates object
        coordinates = FaceCoordinates(parsing)

        return parsing, coordinates

def get_coordinates(image_path: str, checkpoint_path: str = None) -> FaceCoordinates:
    """
    Convenience function to get face coordinates directly
    Args:
        image_path: Path to input image
        checkpoint_path: Optional path to model checkpoint
    Returns:
        FaceCoordinates object with feature locations
    """
    parser = FaceParser(checkpoint_path)
    _, coordinates = parser.parse(image_path)
    return coordinates
