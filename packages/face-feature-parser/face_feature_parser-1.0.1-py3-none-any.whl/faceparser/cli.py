import os
import click
import torch
import requests
from pathlib import Path
from tqdm import tqdm
import cv2
from faceparser import FaceFeatureParser

DEFAULT_MODEL_PATH = os.path.expanduser('~/.faceparser/models/79999_iter.pth')
MODEL_URL = "https://drive.google.com/file/d/1o9BNmFHG7R84JzXSJ9Ev3xPPeursYOI_/view"

def download_file(url: str, destination: str, chunk_size: int = 8192) -> None:
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    with open(destination, 'wb') as f, tqdm(
        desc="Downloading model",
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=chunk_size):
            size = f.write(data)
            pbar.update(size)

@click.group()
def cli():
    """FaceParser CLI tool for face parsing and feature extraction."""
    pass

@cli.command()
@click.option('--model-path', default=DEFAULT_MODEL_PATH,
              help='Path to save the model weights.')
def install(model_path: str):
    """Download and install the face parsing model."""
    try:
        if os.path.exists(model_path):
            click.echo(f"Model already exists at {model_path}")
            return
            
        click.echo("Downloading face parsing model...")
        download_file(MODEL_URL, model_path)
        click.echo(f"Model successfully installed at {model_path}")
    except Exception as e:
        click.echo(f"Error installing model: {str(e)}", err=True)

@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output directory for visualization')
@click.option('--save-masks', is_flag=True, help='Save individual feature masks')
@click.option('--model-path', default=DEFAULT_MODEL_PATH,
              help='Path to the model weights')
def parse(image_path: str, output: str, save_masks: bool, model_path: str):
    """Parse facial features in an image."""
    from .model import FaceParser
    
    try:
        if not os.path.exists(model_path):
            click.echo(f"Model not found at {model_path}. Please run 'faceparser install' first.")
            return

        parser = FaceParser(model_path)
        parsing_map, coordinates = parser.parse(image_path)
        
        if output:
            os.makedirs(output, exist_ok=True)
            # Save visualization
            parser.visualize(parsing_map, save_path=os.path.join(output, "visualization.png"))
            
            if save_masks:
                # Save individual feature masks
                for feature, mask in coordinates.get_feature_masks().items():
                    mask_path = os.path.join(output, f"{feature}_mask.png")
                    parser.save_mask(mask, mask_path)
                
        # Print feature metrics
        metrics = coordinates.get_relative_metrics()
        click.echo("\nFeature Metrics:")
        for feature, area in metrics['feature_areas'].items():
            click.echo(f"{feature}: {area:.3f}")
            
    except Exception as e:
        click.echo(f"Error processing image: {str(e)}", err=True)

@cli.command()
@click.option('--model-path', default=DEFAULT_MODEL_PATH,
              help='Path to check for model installation')
def check(model_path: str):
    """Check if the model is installed."""
    if os.path.exists(model_path):
        click.echo(f"Model is installed at {model_path}")
    else:
        click.echo("Model is not installed. Run 'faceparser install' to install it.")
