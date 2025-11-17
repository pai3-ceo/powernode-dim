"""
Collaborative Pattern Engine - HTTP Server Entry Point
"""

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import yaml
import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent))
from engine import CollaborativeEngine

app = FastAPI(title="DIM Collaborative Pattern Engine", version="1.0.0")

# Load config
config_path = Path(__file__).parent.parent.parent / 'config' / 'dev.yaml'
if config_path.exists():
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
else:
    config = {
        'ipfs': {
            'api_url': '/ip4/127.0.0.1/tcp/5001'
        }
    }

# Create engine
engine = CollaborativeEngine(config)


@app.post('/execute')
async def execute(request: dict):
    """Execute collaborative inference"""
    try:
        job_id = request.get('job_id')
        spec = request.get('spec', {})
        
        if not job_id:
            raise HTTPException(status_code=400, detail="Missing job_id")
        
        result = await engine.execute(job_id, spec)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/health')
async def health():
    """Health check"""
    return {'status': 'ok', 'pattern': 'collaborative'}


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8001)

