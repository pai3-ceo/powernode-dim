/**
 * DIM API Gateway - Main Entry Point
 */

import Fastify from 'fastify';
import websocket from '@fastify/websocket';
import cors from '@fastify/cors';
import { inferenceRoutes } from './routes/inference.js';
import { healthRoutes } from './routes/health.js';
import { setupWebSocket } from './websocket/updates.js';
import { OrchestratorClient } from './grpc/orchestrator-client.js';

// Extend Fastify types
declare module 'fastify' {
  interface FastifyInstance {
    orchestrator: OrchestratorClient;
  }
}

async function start() {
  // Load configuration
  const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    host: process.env.HOST || '0.0.0.0',
    orchestrator: {
      grpcAddress: process.env.ORCHESTRATOR_ADDRESS || 'localhost:50051'
    },
    logLevel: process.env.LOG_LEVEL || 'info'
  };
  
  // Create Fastify server
  const server = Fastify({
    logger: {
      level: config.logLevel
    }
  });
  
  // Register CORS
  await server.register(cors, {
    origin: true,  // In production, restrict this
    credentials: true
  });
  
  // Register WebSocket
  await server.register(websocket);
  
  // Initialize gRPC client to orchestrator
  const orchestratorClient = new OrchestratorClient(
    config.orchestrator.grpcAddress,
    server
  );
  
  // Make client available to routes
  server.decorate('orchestrator', orchestratorClient);
  
  // Register routes
  await server.register(inferenceRoutes);
  await server.register(healthRoutes);
  
  // Setup WebSocket
  await setupWebSocket(server);
  
  // Start server
  try {
    const address = await server.listen({
      port: config.port,
      host: config.host
    });
    
    server.log.info(`DIM API Gateway listening on ${address}`);
  } catch (error: any) {
    server.log.error(`Failed to start API Gateway: ${error.message}`);
    process.exit(1);
  }
}

start().catch((err) => {
  console.error('Failed to start API Gateway:', err);
  process.exit(1);
});

