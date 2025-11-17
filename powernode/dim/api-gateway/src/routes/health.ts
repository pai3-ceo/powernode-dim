/**
 * Health check routes
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

export async function healthRoutes(fastify: FastifyInstance) {
  
  fastify.get('/health', async (request: FastifyRequest, reply: FastifyReply) => {
    return reply.code(200).send({
      status: 'ok',
      service: 'dim-api-gateway',
      version: '1.0.0',
      timestamp: new Date().toISOString()
    });
  });
  
  fastify.get('/health/ready', async (request: FastifyRequest, reply: FastifyReply) => {
    // Check if orchestrator is available
    const orchestratorClient = fastify.orchestrator as any;
    
    // For Phase 1, just return ready
    // In Phase 2, check orchestrator connection
    return reply.code(200).send({
      status: 'ready',
      orchestrator: 'connected'  // Placeholder
    });
  });
}

