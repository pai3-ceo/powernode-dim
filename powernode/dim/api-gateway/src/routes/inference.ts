/**
 * Inference API Routes
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { 
  JobSubmitRequest, 
  JobStatusResponse, 
  JobSubmitResponse,
  JobResultResponse 
} from '../types/index.js';

// Zod schemas for validation
const CollaborativeConfigSchema = z.object({
  modelId: z.string(),
  nodes: z.array(z.string()).min(2),
  dataRequirements: z.object({
    type: z.string(),
    minSamples: z.number().optional(),
    timeRange: z.string().optional()
  }).optional(),
  aggregation: z.object({
    method: z.enum(['federated_averaging', 'weighted_average', 'median']),
    differentialPrivacy: z.object({
      enabled: z.boolean(),
      epsilon: z.number().optional()
    }).optional()
  }),
  reputationMin: z.number().min(0).max(1).optional(),
  timeout: z.number().positive().optional()
});

const ComparativeConfigSchema = z.object({
  modelIds: z.array(z.string()).min(2),
  nodeId: z.string(),
  dataSource: z.string(),
  consensus: z.object({
    method: z.enum(['majority_vote', 'weighted_vote', 'expert_review']),
    minAgreement: z.number().min(0).max(1).optional()
  }),
  timeout: z.number().positive().optional()
});

const PipelineStepSchema = z.object({
  step: z.number().int().positive(),
  name: z.string(),
  modelId: z.string(),
  nodeId: z.string(),
  inputSource: z.string(),
  timeout: z.number().positive().optional()
});

const ChainedConfigSchema = z.object({
  pipeline: z.array(PipelineStepSchema).min(2),
  errorHandling: z.object({
    onFailure: z.enum(['rollback_and_retry', 'fail_fast']).optional(),
    maxRetries: z.number().int().positive().optional()
  }).optional()
});

const JobSubmitRequestSchema = z.object({
  pattern: z.enum(['collaborative', 'comparative', 'chained']),
  config: z.union([CollaborativeConfigSchema, ComparativeConfigSchema, ChainedConfigSchema]),
  priority: z.enum(['low', 'normal', 'high']).optional(),
  maxCost: z.number().int().positive().optional()
});

export async function inferenceRoutes(fastify: FastifyInstance) {
  
  // Submit new inference job
  fastify.post<{ Body: JobSubmitRequest }>('/api/inference/submit', {
    schema: {
      body: JobSubmitRequestSchema,
      response: {
        200: {
          type: 'object',
          properties: {
            jobId: { type: 'string' },
            status: { type: 'string' },
            estimatedCost: { type: 'number' },
            estimatedCompletion: { type: 'string' }
          }
        }
      }
    }
  }, async (request: FastifyRequest<{ Body: JobSubmitRequest }>, reply: FastifyReply) => {
    try {
      // 1. Authenticate (placeholder for Phase 1)
      // const user = await authenticateRequest(request);
      const userId = 'user-123';  // Placeholder
      
      // 2. Validate job spec (Zod already validated via schema)
      const validation = validateJobSpec(request.body);
      if (!validation.valid) {
        return reply.code(400).send({ error: validation.error });
      }
      
      // 3. Forward to orchestrator via gRPC
      const orchestratorClient = fastify.orchestrator as any;
      const jobId = await orchestratorClient.submitJob(request.body, userId);
      
      // 4. Return job ID
      const response: JobSubmitResponse = {
        jobId,
        status: 'pending',
        estimatedCost: 2400,  // Placeholder
        estimatedCompletion: new Date(Date.now() + 300000).toISOString()  // 5 min from now
      };
      
      return reply.code(200).send(response);
    } catch (error: any) {
      fastify.log.error(`Error submitting job: ${error.message}`);
      return reply.code(500).send({ error: error.message });
    }
  });
  
  // Get job status
  fastify.get<{ Params: { jobId: string } }>('/api/inference/status/:jobId', 
    async (request: FastifyRequest<{ Params: { jobId: string } }>, reply: FastifyReply) => {
      try {
        const { jobId } = request.params;
        const orchestratorClient = fastify.orchestrator as any;
        const status = await orchestratorClient.getJobStatus(jobId);
        return reply.code(200).send(status);
      } catch (error: any) {
        fastify.log.error(`Error getting job status: ${error.message}`);
        return reply.code(500).send({ error: error.message });
      }
    }
  );
  
  // Cancel job
  fastify.delete<{ Params: { jobId: string } }>('/api/inference/job/:jobId',
    async (request: FastifyRequest<{ Params: { jobId: string } }>, reply: FastifyReply) => {
      try {
        const { jobId } = request.params;
        const orchestratorClient = fastify.orchestrator as any;
        await orchestratorClient.cancelJob(jobId);
        return reply.code(200).send({ success: true });
      } catch (error: any) {
        fastify.log.error(`Error cancelling job: ${error.message}`);
        return reply.code(500).send({ error: error.message });
      }
    }
  );
  
  // Get job result
  fastify.get<{ Params: { jobId: string } }>('/api/inference/result/:jobId',
    async (request: FastifyRequest<{ Params: { jobId: string } }>, reply: FastifyReply) => {
      try {
        const { jobId } = request.params;
        const orchestratorClient = fastify.orchestrator as any;
        const result = await orchestratorClient.getJobResult(jobId);
        return reply.code(200).send(result);
      } catch (error: any) {
        fastify.log.error(`Error getting job result: ${error.message}`);
        return reply.code(500).send({ error: error.message });
      }
    }
  );
}

function validateJobSpec(request: JobSubmitRequest): { valid: boolean; error?: string } {
  // Additional validation beyond Zod schema
  try {
    if (request.pattern === 'collaborative') {
      const config = request.config as any;
      if (!config.nodes || config.nodes.length < 2) {
        return { valid: false, error: 'Collaborative requires at least 2 nodes' };
      }
    } else if (request.pattern === 'comparative') {
      const config = request.config as any;
      if (!config.modelIds || config.modelIds.length < 2) {
        return { valid: false, error: 'Comparative requires at least 2 models' };
      }
    } else if (request.pattern === 'chained') {
      const config = request.config as any;
      if (!config.pipeline || config.pipeline.length < 2) {
        return { valid: false, error: 'Chained requires at least 2 pipeline steps' };
      }
    }
    
    return { valid: true };
  } catch (error: any) {
    return { valid: false, error: error.message };
  }
}

