# DIM Test Cases

Comprehensive test case documentation for DIM module.

## Test Case Categories

### 1. Orchestrator Tests

#### TC-ORCH-001: Orchestrator Initialization
- **Description**: Verify orchestrator initializes correctly
- **Preconditions**: Valid configuration
- **Steps**: Create DIMOrchestrator instance
- **Expected**: All components initialized, no errors

#### TC-ORCH-002: Job Submission
- **Description**: Submit job through orchestrator
- **Preconditions**: Orchestrator running
- **Steps**: Submit collaborative job
- **Expected**: Job ID returned, job in active_jobs

#### TC-ORCH-003: Job Status Retrieval
- **Description**: Get job status
- **Preconditions**: Job submitted
- **Steps**: Call get_job_status
- **Expected**: Status returned with correct state

#### TC-ORCH-004: Job Cancellation
- **Description**: Cancel running job
- **Preconditions**: Job in pending/running state
- **Steps**: Call cancel_job
- **Expected**: Job state set to CANCELLED

#### TC-ORCH-005: Job Validation
- **Description**: Validate job specifications
- **Preconditions**: None
- **Steps**: Submit invalid job specs
- **Expected**: Validation errors returned

#### TC-ORCH-006: Node Selection
- **Description**: Select nodes for job
- **Preconditions**: Nodes in registry
- **Steps**: Call select_nodes with requirements
- **Expected**: Appropriate nodes selected

#### TC-ORCH-007: Job Distribution
- **Description**: Distribute job to another orchestrator
- **Preconditions**: Multiple orchestrators available
- **Steps**: Submit job when local load high
- **Expected**: Job assigned to another orchestrator

### 2. Daemon Tests

#### TC-DAEMON-001: Daemon Initialization
- **Description**: Verify daemon initializes correctly
- **Preconditions**: Valid configuration
- **Steps**: Create DIMDaemon instance
- **Expected**: All components initialized

#### TC-DAEMON-002: Job Submission to Daemon
- **Description**: Submit job to daemon
- **Preconditions**: Daemon running, resources available
- **Steps**: Submit job via gRPC
- **Expected**: Job queued, status returned

#### TC-DAEMON-003: Job Execution
- **Description**: Execute inference job
- **Preconditions**: Job queued, model available
- **Steps**: Process job from queue
- **Expected**: Job executed, result returned

#### TC-DAEMON-004: Resource Management
- **Description**: Check resource availability
- **Preconditions**: Daemon running
- **Steps**: Submit job when resources low
- **Expected**: Resource error or queued

#### TC-DAEMON-005: Model Caching
- **Description**: Cache model from IPFS
- **Preconditions**: Model in IPFS
- **Steps**: Request model
- **Expected**: Model downloaded and cached

#### TC-DAEMON-006: Health Check
- **Description**: Get daemon health status
- **Preconditions**: Daemon running
- **Steps**: Call get_health
- **Expected**: Health status with resources

#### TC-DAEMON-007: Statistics
- **Description**: Get daemon statistics
- **Preconditions**: Daemon has processed jobs
- **Steps**: Call get_stats
- **Expected**: Statistics returned

### 3. Pattern Engine Tests

#### TC-PATTERN-001: Collaborative Pattern
- **Description**: Execute collaborative pattern
- **Preconditions**: Multiple nodes available
- **Steps**: Submit collaborative job
- **Expected**: Results aggregated from all nodes

#### TC-PATTERN-002: Comparative Pattern
- **Description**: Execute comparative pattern
- **Preconditions**: Multiple models available
- **Steps**: Submit comparative job
- **Expected**: Consensus built from all models

#### TC-PATTERN-003: Chained Pattern
- **Description**: Execute chained pattern
- **Preconditions**: Pipeline steps defined
- **Steps**: Submit chained job
- **Expected**: Steps executed sequentially

### 4. IPFS Integration Tests

#### TC-IPFS-001: Save Job Spec
- **Description**: Save job spec to IPFS
- **Preconditions**: IPFS running
- **Steps**: Save job spec
- **Expected**: CID returned

#### TC-IPFS-002: Load Job Result
- **Description**: Load job result from IPFS
- **Preconditions**: Result saved to IPFS
- **Steps**: Load result by CID
- **Expected**: Result data returned

#### TC-IPFS-003: IPNS State Update
- **Description**: Update state via IPNS
- **Preconditions**: IPNS key created
- **Steps**: Update node registry
- **Expected**: IPNS name returned

#### TC-IPFS-004: Pubsub Publish
- **Description**: Publish event via Pubsub
- **Preconditions**: IPFS Pubsub enabled
- **Steps**: Publish job event
- **Expected**: Event published successfully

#### TC-IPFS-005: Pubsub Subscribe
- **Description**: Subscribe to Pubsub topic
- **Preconditions**: IPFS Pubsub enabled
- **Steps**: Subscribe to job updates
- **Expected**: Subscription active

### 5. Node Discovery Tests

#### TC-DISCOVERY-001: Node Registration
- **Description**: Register node in registry
- **Preconditions**: IPNS available
- **Steps**: Register node
- **Expected**: Node in registry

#### TC-DISCOVERY-002: Node Heartbeat
- **Description**: Update node heartbeat
- **Preconditions**: Node registered
- **Steps**: Send heartbeat
- **Expected**: Heartbeat updated in registry

#### TC-DISCOVERY-003: Stale Node Detection
- **Description**: Detect stale nodes
- **Preconditions**: Node not sending heartbeats
- **Steps**: Wait for timeout
- **Expected**: Node marked as stale/inactive

#### TC-DISCOVERY-004: Node Discovery
- **Description**: Discover active nodes
- **Preconditions**: Nodes sending heartbeats
- **Steps**: Call discover_nodes
- **Expected**: Active nodes returned

### 6. Performance Tests

#### TC-PERF-001: Concurrent Job Submission
- **Description**: Submit multiple jobs concurrently
- **Preconditions**: Orchestrator running
- **Steps**: Submit 100 jobs concurrently
- **Expected**: All jobs accepted, no errors

#### TC-PERF-002: Job Submission Throughput
- **Description**: Measure job submission rate
- **Preconditions**: Orchestrator running
- **Steps**: Submit 1000 jobs sequentially
- **Expected**: > 100 jobs/second

#### TC-PERF-003: Node Selection Performance
- **Description**: Measure node selection speed
- **Preconditions**: Large node registry (100+ nodes)
- **Steps**: Select nodes 100 times
- **Expected**: < 1 second for 100 selections

#### TC-PERF-004: Model Pre-warming Impact
- **Description**: Measure inference time with/without pre-warming
- **Preconditions**: Model pre-warmer enabled
- **Steps**: Run inference on pre-warmed model
- **Expected**: Faster inference time

#### TC-PERF-005: Connection Pool Efficiency
- **Description**: Measure connection reuse impact
- **Preconditions**: Connection pool enabled
- **Steps**: Make 100 gRPC calls
- **Expected**: Connections reused, faster response

### 7. Security Tests

#### TC-SEC-001: Rate Limiting Enforcement
- **Description**: Verify rate limiting works
- **Preconditions**: Rate limiting enabled
- **Steps**: Exceed rate limit
- **Expected**: Requests rejected with rate limit error

#### TC-SEC-002: Per-User Rate Limits
- **Description**: Verify per-user limits
- **Preconditions**: User limits configured
- **Steps**: Exceed user-specific limit
- **Expected**: User-specific rate limit applied

#### TC-SEC-003: TLS Server Configuration
- **Description**: Verify TLS server setup
- **Preconditions**: TLS enabled, certificates available
- **Steps**: Start gRPC server
- **Expected**: Server starts with TLS

#### TC-SEC-004: TLS Client Configuration
- **Description**: Verify TLS client setup
- **Preconditions**: TLS enabled, CA available
- **Steps**: Connect to TLS server
- **Expected**: Secure connection established

#### TC-SEC-005: Input Validation
- **Description**: Verify input validation
- **Preconditions**: None
- **Steps**: Submit invalid job spec
- **Expected**: Validation error returned

### 8. Integration Tests

#### TC-INT-001: Orchestrator-Daemon Communication
- **Description**: Test orchestrator-daemon gRPC communication
- **Preconditions**: Both services running
- **Steps**: Submit job from orchestrator to daemon
- **Expected**: Job received and processed

#### TC-INT-002: Pattern Engine-Orchestrator Communication
- **Description**: Test pattern engine-orchestrator communication
- **Preconditions**: Both services running
- **Steps**: Orchestrator calls pattern engine
- **Expected**: Pattern executed successfully

#### TC-INT-003: IPFS State Synchronization
- **Description**: Test state sync via IPFS
- **Preconditions**: Multiple orchestrators
- **Steps**: Update state on one orchestrator
- **Expected**: State visible to other orchestrators

### 9. End-to-End Tests

#### TC-E2E-001: Complete Collaborative Workflow
- **Description**: Full collaborative pattern workflow
- **Preconditions**: All services running
- **Steps**: Submit job → Execute → Get result
- **Expected**: Complete workflow succeeds

#### TC-E2E-002: Complete Comparative Workflow
- **Description**: Full comparative pattern workflow
- **Preconditions**: All services running
- **Steps**: Submit job → Execute → Get result
- **Expected**: Complete workflow succeeds

#### TC-E2E-003: Complete Chained Workflow
- **Description**: Full chained pattern workflow
- **Preconditions**: All services running
- **Steps**: Submit job → Execute → Get result
- **Expected**: Complete workflow succeeds

#### TC-E2E-004: Multi-Node Workflow
- **Description**: Workflow across multiple nodes
- **Preconditions**: Multiple daemons running
- **Steps**: Submit collaborative job
- **Expected**: Job distributed across nodes

#### TC-E2E-005: Error Recovery
- **Description**: Test error recovery in workflow
- **Preconditions**: All services running
- **Steps**: Simulate node failure
- **Expected**: Job retried on different node

## Test Execution Matrix

| Test Case | Unit | Integration | E2E | Performance | Security |
|-----------|------|-------------|-----|-------------|----------|
| TC-ORCH-001 | ✅ | | | | |
| TC-ORCH-002 | ✅ | ✅ | ✅ | | |
| TC-ORCH-003 | ✅ | ✅ | | | |
| TC-ORCH-004 | ✅ | ✅ | | | |
| TC-ORCH-005 | ✅ | | | | |
| TC-ORCH-006 | ✅ | ✅ | | ✅ | |
| TC-ORCH-007 | | ✅ | ✅ | | |
| TC-DAEMON-001 | ✅ | | | | |
| TC-DAEMON-002 | ✅ | ✅ | ✅ | | |
| TC-DAEMON-003 | ✅ | ✅ | ✅ | | |
| TC-DAEMON-004 | ✅ | ✅ | | | |
| TC-DAEMON-005 | ✅ | ✅ | | ✅ | |
| TC-DAEMON-006 | ✅ | ✅ | | | |
| TC-DAEMON-007 | ✅ | ✅ | | | |
| TC-PATTERN-001 | ✅ | ✅ | ✅ | | |
| TC-PATTERN-002 | ✅ | ✅ | ✅ | | |
| TC-PATTERN-003 | ✅ | ✅ | ✅ | | |
| TC-IPFS-001 | ✅ | ✅ | | | |
| TC-IPFS-002 | ✅ | ✅ | | | |
| TC-IPFS-003 | ✅ | ✅ | | | |
| TC-IPFS-004 | ✅ | ✅ | | | |
| TC-IPFS-005 | ✅ | ✅ | | | |
| TC-DISCOVERY-001 | ✅ | ✅ | | | |
| TC-DISCOVERY-002 | ✅ | ✅ | | | |
| TC-DISCOVERY-003 | ✅ | ✅ | | | |
| TC-DISCOVERY-004 | ✅ | ✅ | | | |
| TC-PERF-001 | | | | ✅ | |
| TC-PERF-002 | | | | ✅ | |
| TC-PERF-003 | | | | ✅ | |
| TC-PERF-004 | | | | ✅ | |
| TC-PERF-005 | | | | ✅ | |
| TC-SEC-001 | ✅ | | | | ✅ |
| TC-SEC-002 | ✅ | | | | ✅ |
| TC-SEC-003 | ✅ | ✅ | | | ✅ |
| TC-SEC-004 | ✅ | ✅ | | | ✅ |
| TC-SEC-005 | ✅ | | | | ✅ |
| TC-INT-001 | | ✅ | ✅ | | |
| TC-INT-002 | | ✅ | ✅ | | |
| TC-INT-003 | | ✅ | | | |
| TC-E2E-001 | | | ✅ | | |
| TC-E2E-002 | | | ✅ | | |
| TC-E2E-003 | | | ✅ | | |
| TC-E2E-004 | | | ✅ | | |
| TC-E2E-005 | | | ✅ | | |

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths
- **E2E Tests**: All three patterns
- **Performance Tests**: Key metrics validated
- **Security Tests**: All security features

## Test Data Requirements

### Models
- Small model (< 100MB)
- Medium model (100-500MB)
- Large model (> 500MB)
- Different formats (MLX, CoreML, PyTorch, ONNX)

### Jobs
- Valid job specifications (all patterns)
- Invalid job specifications (for validation tests)
- Edge cases (empty configs, missing fields)

### Nodes
- Active nodes
- Inactive nodes
- Stale nodes
- Various capabilities

