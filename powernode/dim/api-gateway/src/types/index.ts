/**
 * TypeScript types for DIM API Gateway
 */

export type Pattern = 'collaborative' | 'comparative' | 'chained';
export type Priority = 'low' | 'normal' | 'high';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface JobSubmitRequest {
  pattern: Pattern;
  config: CollaborativeConfig | ComparativeConfig | ChainedConfig;
  priority?: Priority;
  maxCost?: number;  // Max $PAI3 tokens
}

export interface CollaborativeConfig {
  modelId: string;
  nodes: string[];  // Node IDs
  dataRequirements?: {
    type: string;
    minSamples?: number;
    timeRange?: string;
  };
  aggregation: {
    method: 'federated_averaging' | 'weighted_average' | 'median';
    differentialPrivacy?: {
      enabled: boolean;
      epsilon?: number;
    };
  };
  reputationMin?: number;
  timeout?: number;
}

export interface ComparativeConfig {
  modelIds: string[];
  nodeId: string;
  dataSource: string;
  consensus: {
    method: 'majority_vote' | 'weighted_vote' | 'expert_review';
    minAgreement?: number;
  };
  timeout?: number;
}

export interface PipelineStep {
  step: number;
  name: string;
  modelId: string;
  nodeId: string;
  inputSource: 'client_data' | string;  // 'step_1_output', etc.
  timeout?: number;  // seconds
}

export interface ChainedConfig {
  pipeline: PipelineStep[];
  errorHandling?: {
    onFailure?: 'rollback_and_retry' | 'fail_fast';
    maxRetries?: number;
  };
}

export interface JobSubmitResponse {
  jobId: string;
  status: JobStatus;
  estimatedCost?: number;
  estimatedCompletion?: string;  // ISO 8601 date
}

export interface JobStatusResponse {
  jobId: string;
  status: JobStatus;
  pattern: Pattern;
  progress: {
    completedSteps: number;
    totalSteps: number;
    percentComplete: number;
  };
  estimatedCompletion?: string;
  costActual?: number;
  nodes?: Array<{
    nodeId: string;
    status: string;
    executionTime?: string;
  }>;
  result?: any;
  error?: string;
}

export interface JobResultResponse {
  jobId: string;
  result: any;
  metadata: {
    nodesUsed: number;
    totalExecutionTime: string;
    totalCost: number;
  };
}

