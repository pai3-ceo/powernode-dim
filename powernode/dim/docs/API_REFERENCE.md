# DIM API Reference

## REST API (API Gateway)

**Base URL**: `http://localhost:3000`

### Submit Job

```http
POST /api/inference/submit
Content-Type: application/json

{
  "pattern": "collaborative" | "comparative" | "chained",
  "config": {
    // Pattern-specific configuration
  },
  "priority": "low" | "normal" | "high",
  "maxCost": 5000
}
```

**Response:**
```json
{
  "jobId": "job-abc123def456",
  "status": "pending",
  "estimatedCost": 2400,
  "estimatedCompletion": "2025-11-16T15:30:00Z"
}
```

### Get Job Status

```http
GET /api/inference/status/{jobId}
```

**Response:**
```json
{
  "jobId": "job-abc123def456",
  "status": "running",
  "pattern": "collaborative",
  "progress": {
    "completedSteps": 3,
    "totalSteps": 5,
    "percentComplete": 60
  },
  "estimatedCompletion": "2025-11-16T15:35:00Z",
  "costActual": 1200,
  "nodes": [
    {
      "nodeId": "node-001",
      "status": "completed",
      "executionTime": "45s"
    }
  ]
}
```

### Get Job Result

```http
GET /api/inference/result/{jobId}
```

**Response:**
```json
{
  "jobId": "job-abc123def456",
  "result": {
    // Pattern-specific result
  },
  "metadata": {
    "nodesUsed": 5,
    "totalExecutionTime": "125s",
    "totalCost": 2350
  }
}
```

### Cancel Job

```http
DELETE /api/inference/job/{jobId}
```

**Response:**
```json
{
  "success": true
}
```

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "dim-api-gateway",
  "version": "1.0.0",
  "timestamp": "2024-12-19T10:00:00Z"
}
```

## WebSocket API

### Connect to Job Updates

```javascript
const ws = new WebSocket('ws://localhost:3000/ws/jobs/{jobId}');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // {
  //   "jobId": "job-abc123",
  //   "status": "running",
  //   "progress": {...},
  //   "timestamp": "2024-12-19T10:00:00Z"
  // }
};
```

## Pattern Configurations

### Collaborative Pattern

```json
{
  "pattern": "collaborative",
  "config": {
    "modelId": "model-abc123",
    "nodes": ["node-001", "node-002", "node-003"],
    "dataRequirements": {
      "type": "medical",
      "minSamples": 100
    },
    "aggregation": {
      "method": "federated_averaging",
      "differentialPrivacy": {
        "enabled": true,
        "epsilon": 1.0
      }
    },
    "reputationMin": 0.85,
    "timeout": 120
  }
}
```

### Comparative Pattern

```json
{
  "pattern": "comparative",
  "config": {
    "modelIds": ["model-001", "model-002", "model-003"],
    "nodeId": "node-001",
    "dataSource": "cabinet-abc123",
    "consensus": {
      "method": "weighted_vote",
      "minAgreement": 0.75
    },
    "timeout": 120
  }
}
```

### Chained Pattern

```json
{
  "pattern": "chained",
  "config": {
    "pipeline": [
      {
        "step": 1,
        "name": "Triage",
        "modelId": "model-triage",
        "nodeId": "node-001",
        "inputSource": "client_data",
        "timeout": 60
      },
      {
        "step": 2,
        "name": "Diagnosis",
        "modelId": "model-diagnosis",
        "nodeId": "node-001",
        "inputSource": "step_1_output",
        "timeout": 120
      },
      {
        "step": 3,
        "name": "Treatment",
        "modelId": "model-treatment",
        "nodeId": "node-002",
        "inputSource": "step_2_output",
        "timeout": 120
      }
    ],
    "errorHandling": {
      "onFailure": "rollback_and_retry",
      "maxRetries": 2
    }
  }
}
```

## gRPC API (Phase 2)

See `proto/` directory for complete Protocol Buffer definitions.

### Orchestrator Service

- `SubmitJob(SubmitJobRequest) → SubmitJobResponse`
- `GetJobStatus(GetJobStatusRequest) → JobStatusResponse`
- `CancelJob(CancelJobRequest) → CancelJobResponse`
- `GetJobResult(GetJobResultRequest) → JobResultResponse`
- `ListJobs(ListJobsRequest) → ListJobsResponse`

### Daemon Service

- `SubmitJob(SubmitJobRequest) → SubmitJobResponse`
- `GetJobStatus(GetJobStatusRequest) → JobStatusResponse`
- `CancelJob(CancelJobRequest) → CancelJobResponse`
- `GetHealth(GetHealthRequest) → HealthResponse`
- `GetStats(GetStatsRequest) → StatsResponse`

## Error Responses

All APIs return standard error responses:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

