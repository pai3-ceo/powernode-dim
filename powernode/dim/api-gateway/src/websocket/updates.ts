/**
 * WebSocket for real-time job updates
 */

import { FastifyInstance } from 'fastify';
import { WebSocket } from 'ws';

export async function setupWebSocket(fastify: FastifyInstance) {
  
  fastify.get('/ws/jobs/:jobId', { websocket: true }, 
    (connection: any, req: any) => {
      const jobId = req.params.jobId;
      
      fastify.log.info(`WebSocket connection opened for job ${jobId}`);
      
      // Subscribe to job updates from IPFS Pubsub
      // For Phase 1, this is a placeholder
      // In Phase 2, subscribe to IPFS Pubsub topic: dim.jobs.{jobId}.updates
      
      // Mock: send periodic updates
      const interval = setInterval(() => {
        if (connection.socket.readyState === WebSocket.OPEN) {
          connection.socket.send(JSON.stringify({
            jobId,
            status: 'running',
            progress: {
              completedSteps: 1,
              totalSteps: 5,
              percentComplete: 20
            },
            timestamp: new Date().toISOString()
          }));
        }
      }, 5000);  // Every 5 seconds
      
      connection.socket.on('close', () => {
        fastify.log.info(`WebSocket connection closed for job ${jobId}`);
        clearInterval(interval);
      });
      
      connection.socket.on('error', (error: Error) => {
        fastify.log.error(`WebSocket error for job ${jobId}: ${error.message}`);
        clearInterval(interval);
      });
    }
  );
}

