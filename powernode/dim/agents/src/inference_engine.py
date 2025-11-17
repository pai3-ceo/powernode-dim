"""
Inference Engine - Model loading and inference
Supports multiple formats: MLX, CoreML, PyTorch, ONNX
"""

from typing import Dict, Any, Optional
import os
from pathlib import Path
from .loaders.mlx_loader import MLXLoader
from .loaders.coreml_loader import CoreMLLoader
from .loaders.pytorch_loader import PyTorchLoader
from .loaders.onnx_loader import ONNXLoader


class InferenceEngine:
    """
    Model inference engine
    
    Supports multiple formats:
    - MLX (Apple Silicon optimized)
    - CoreML
    - PyTorch
    - ONNX
    """
    
    def __init__(self, model_path: str):
        """
        Initialize inference engine
        
        Args:
            model_path: Path to model file
        """
        self.model_path = model_path
        self.model = None
        self.model_type = self.detect_model_type(model_path)
        
        # Load model
        self.load_model()
    
    def detect_model_type(self, model_path: str) -> str:
        """
        Detect model type from file extension
        
        Args:
            model_path: Path to model file
            
        Returns:
            Model type string
        """
        ext = os.path.splitext(model_path)[1].lower()
        
        if ext == '.mlx':
            return 'mlx'
        elif ext in ['.mlmodelc', '.mlpackage']:
            return 'coreml'
        elif ext in ['.pt', '.pth']:
            return 'pytorch'
        elif ext == '.onnx':
            return 'onnx'
        else:
            # Default to PyTorch for unknown extensions
            return 'pytorch'
    
    def load_model(self):
        """Load model using appropriate loader"""
        if self.model_type == 'mlx':
            loader = MLXLoader()
            self.model = loader.load(self.model_path)
            
        elif self.model_type == 'coreml':
            loader = CoreMLLoader()
            self.model = loader.load(self.model_path)
            
        elif self.model_type == 'pytorch':
            loader = PyTorchLoader()
            self.model = loader.load(self.model_path)
            
        elif self.model_type == 'onnx':
            loader = ONNXLoader()
            self.model = loader.load(self.model_path)
    
    def infer(self, input_data: Any) -> Dict:
        """
        Run inference
        
        Args:
            input_data: Input data (format depends on model)
            
        Returns:
            Inference result dictionary
        """
        if self.model_type == 'mlx':
            return self._infer_mlx(input_data)
        elif self.model_type == 'coreml':
            return self._infer_coreml(input_data)
        elif self.model_type == 'pytorch':
            return self._infer_pytorch(input_data)
        elif self.model_type == 'onnx':
            return self._infer_onnx(input_data)
    
    def _infer_mlx(self, input_data):
        """MLX inference"""
        try:
            import mlx.core as mx
            
            # Convert input to MLX array
            if isinstance(input_data, dict):
                # Handle structured input
                input_tensor = mx.array(input_data.get('data', input_data))
            else:
                input_tensor = mx.array(input_data)
            
            # Run inference
            output = self.model(input_tensor)
            
            # Convert output
            return {
                'output': output.tolist() if hasattr(output, 'tolist') else str(output),
                'model_type': 'mlx'
            }
        except Exception as e:
            return {
                'error': f"MLX inference failed: {str(e)}",
                'model_type': 'mlx'
            }
    
    def _infer_coreml(self, input_data):
        """CoreML inference"""
        try:
            import coremltools as ct
            
            # Convert input
            if isinstance(input_data, dict):
                # CoreML expects specific input format
                input_dict = {k: ct.models.MLFeatureValue(value=v) for k, v in input_data.items()}
            else:
                # Single input
                input_dict = {'input': ct.models.MLFeatureValue(value=input_data)}
            
            # Run inference
            output = self.model.predict(input_dict)
            
            # Convert output
            return {
                'output': output,
                'model_type': 'coreml'
            }
        except Exception as e:
            return {
                'error': f"CoreML inference failed: {str(e)}",
                'model_type': 'coreml'
            }
    
    def _infer_pytorch(self, input_data):
        """PyTorch inference (with MPS backend for M4 Pro)"""
        try:
            import torch
            
            # Use MPS (Metal Performance Shaders) for GPU acceleration
            device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
            
            # Move model to device
            self.model.to(device)
            self.model.eval()
            
            # Convert input
            if isinstance(input_data, dict):
                input_tensor = torch.tensor(input_data.get('data', input_data)).to(device)
            else:
                input_tensor = torch.tensor(input_data).to(device)
            
            # Run inference
            with torch.no_grad():
                output = self.model(input_tensor)
            
            # Convert output
            return {
                'output': output.cpu().numpy().tolist() if hasattr(output, 'cpu') else str(output),
                'model_type': 'pytorch',
                'device': str(device)
            }
        except Exception as e:
            return {
                'error': f"PyTorch inference failed: {str(e)}",
                'model_type': 'pytorch'
            }
    
    def _infer_onnx(self, input_data):
        """ONNX inference"""
        try:
            import onnxruntime as ort
            import numpy as np
            
            # Create ONNX Runtime session
            session = ort.InferenceSession(self.model_path)
            
            # Get input name
            input_name = session.get_inputs()[0].name
            
            # Convert input
            if isinstance(input_data, dict):
                input_array = np.array(input_data.get('data', input_data))
            else:
                input_array = np.array(input_data)
            
            # Run inference
            output = session.run(None, {input_name: input_array})
            
            # Convert output
            return {
                'output': output[0].tolist() if len(output) > 0 else str(output),
                'model_type': 'onnx'
            }
        except Exception as e:
            return {
                'error': f"ONNX inference failed: {str(e)}",
                'model_type': 'onnx'
            }

