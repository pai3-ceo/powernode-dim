# DIM Inference Patterns

Detailed documentation for the three inference patterns supported by DIM.

## Collaborative Pattern

**Definition**: Same model on different data sets (data parallel)

### Use Cases

- **Drug Discovery**: Analyze patient data across multiple hospitals
- **Federated Learning**: Train models on distributed data
- **Privacy-Preserving Analytics**: Aggregate insights without sharing raw data

### How It Works

1. **Distribution**: Same model is sent to multiple nodes
2. **Parallel Execution**: Each node processes its own data
3. **Aggregation**: Results are combined using specified method
4. **Privacy**: Data never leaves the node

### Aggregation Methods

#### Federated Averaging
- Averages results from all nodes
- Weighted by data size (optional)
- Most common for federated learning

#### Weighted Average
- Averages with custom weights
- Weights based on node reputation or data quality
- Useful for heterogeneous data

#### Median
- Takes median of all results
- Robust to outliers
- Good for noisy data

#### Differential Privacy
- Adds noise to protect privacy
- Configurable epsilon parameter
- Trade-off between privacy and accuracy

### Example

```json
{
  "pattern": "collaborative",
  "config": {
    "modelId": "drug-discovery-model",
    "nodes": ["hospital-001", "hospital-002", "hospital-003"],
    "dataRequirements": {
      "type": "patient_data",
      "minSamples": 100,
      "timeRange": "2024-01-01/2024-12-31"
    },
    "aggregation": {
      "method": "federated_averaging",
      "differentialPrivacy": {
        "enabled": true,
        "epsilon": 1.0
      }
    },
    "reputationMin": 0.90
  }
}
```

## Comparative Pattern

**Definition**: Different models on same data set (model parallel)

### Use Cases

- **Medical Diagnosis**: Multiple diagnostic models on patient data
- **Model Validation**: Compare model outputs
- **Ensemble Methods**: Combine predictions from multiple models

### How It Works

1. **Model Loading**: Load multiple models on single node
2. **Parallel Execution**: Run all models on same data
3. **Consensus Building**: Combine model outputs
4. **Result**: Consensus prediction

### Consensus Methods

#### Majority Vote
- Most common prediction wins
- Simple and fast
- Good for classification tasks

#### Weighted Vote
- Votes weighted by model reputation
- More accurate models have more weight
- Better for heterogeneous models

#### Expert Review
- Human review if no consensus
- Highest accuracy but slower
- Used for critical decisions

### Example

```json
{
  "pattern": "comparative",
  "config": {
    "modelIds": [
      "diagnosis-model-v1",
      "diagnosis-model-v2",
      "diagnosis-model-v3"
    ],
    "nodeId": "node-001",
    "dataSource": "patient-cabinet-123",
    "consensus": {
      "method": "weighted_vote",
      "minAgreement": 0.75
    }
  }
}
```

## Chained Pattern

**Definition**: Sequential pipeline of models (workflow)

### Use Cases

- **Clinical Workflow**: Triage → Diagnosis → Treatment → Medication
- **Document Processing**: OCR → Classification → Extraction → Analysis
- **Multi-Stage Analysis**: Preprocessing → Feature Extraction → Prediction

### How It Works

1. **Sequential Execution**: Steps run in order
2. **Data Flow**: Output of step N becomes input of step N+1
3. **Error Handling**: Rollback or fail-fast on errors
4. **Transparency**: All intermediate results included

### Error Handling

#### Rollback and Retry
- Retry failed step
- Rollback to previous step if needed
- Configurable max retries

#### Fail Fast
- Stop pipeline on first error
- Return error immediately
- Fastest failure detection

### Example

```json
{
  "pattern": "chained",
  "config": {
    "pipeline": [
      {
        "step": 1,
        "name": "Triage",
        "modelId": "triage-model",
        "nodeId": "node-001",
        "inputSource": "client_data",
        "timeout": 60
      },
      {
        "step": 2,
        "name": "Diagnosis",
        "modelId": "diagnosis-model",
        "nodeId": "node-001",
        "inputSource": "step_1_output",
        "timeout": 120
      },
      {
        "step": 3,
        "name": "Treatment Plan",
        "modelId": "treatment-model",
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

## Pattern Selection Guide

### When to Use Collaborative

- ✅ Data is distributed across nodes
- ✅ Privacy is critical
- ✅ Need to aggregate insights
- ✅ Same model works for all data

### When to Use Comparative

- ✅ Have multiple models to compare
- ✅ Need consensus/validation
- ✅ Data is in one location
- ✅ Want ensemble predictions

### When to Use Chained

- ✅ Multi-stage workflow
- ✅ Sequential processing required
- ✅ Need intermediate results
- ✅ Pipeline with dependencies

## Performance Considerations

### Collaborative
- **Speed**: Fast (parallel execution)
- **Network**: Low (only model transfer)
- **Scalability**: Excellent (add more nodes)

### Comparative
- **Speed**: Medium (sequential model execution)
- **Network**: Very Low (single node)
- **Scalability**: Limited (single node)

### Chained
- **Speed**: Slow (sequential steps)
- **Network**: Medium (step outputs)
- **Scalability**: Good (can distribute steps)

## Best Practices

1. **Choose Right Pattern**: Match pattern to use case
2. **Optimize Timeouts**: Set appropriate timeouts per step
3. **Handle Errors**: Configure error handling strategy
4. **Monitor Performance**: Track execution times
5. **Use Reputation**: Select nodes with high reputation

