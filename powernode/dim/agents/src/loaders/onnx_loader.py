"""
ONNX Loader
"""

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


class ONNXLoader:
    """Load ONNX models"""
    
    def load(self, model_path: str):
        """
        Load ONNX model
        
        Args:
            model_path: Path to ONNX model file
            
        Returns:
            ONNX model path (ONNX Runtime uses path directly)
        """
        if not ONNX_AVAILABLE:
            raise ImportError("ONNX Runtime not available. Install with: pip install onnxruntime")
        
        # ONNX Runtime loads models by path, so we return the path
        # The InferenceEngine will create the session
        return model_path

