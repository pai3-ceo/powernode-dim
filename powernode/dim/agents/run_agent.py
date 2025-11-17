"""
Agent Entry Point - Spawned by daemon for inference execution
"""

import sys
import json
from pathlib import Path

# Add agents src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.inference_engine import InferenceEngine


def main():
    """Main entry point for agent process"""
    # For Phase 1, this is a simple entry point
    # In production, this would receive job spec via stdin or IPC
    
    if len(sys.argv) < 2:
        print("Usage: run_agent.py <model_path> [input_data_json]")
        sys.exit(1)
    
    model_path = sys.argv[1]
    input_data = {}
    
    if len(sys.argv) > 2:
        input_data = json.loads(sys.argv[2])
    
    # Initialize inference engine
    engine = InferenceEngine(model_path)
    
    # Run inference
    result = engine.infer(input_data)
    
    # Output result as JSON
    print(json.dumps(result))
    
    sys.exit(0)


if __name__ == '__main__':
    main()

