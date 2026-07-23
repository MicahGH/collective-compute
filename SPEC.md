# CollectiveCompute Specification

## 1. Introduction

### What is CollectiveCompute?
CollectiveCompute is a decentralised network that allows providers to rent out their GPU compute to clients for running open-source large language models (LLMs). Providers can configure the percentage of GPU resources they are willing to share, as well as the time periods during which those resources are available. Clients interact with the network through a simple API and are not required to provision or manage any GPU infrastructure.

### Who is it for?
#### Providers
Users who want to earn passive income by sharing unused GPU compute with the network. Providers can control how much of their GPU is shared and when it is available.

#### Clients
Users who want to run open-source LLMs but do not have access to sufficient local GPU resources. Instead of purchasing and maintaining expensive hardware, clients can pay providers for on-demand access to GPU compute.

### What problem does it solve?
Running open-source LLMs locally requires a powerful GPU, which many users do not have. Cloud inference providers are a convenient alternative, but they require users to rely on centralised infrastructure and ongoing subscription or usage costs.

At the same time, many consumer GPUs remain unused for large parts of the day. CollectiveCompute allows that unused compute to be shared with other users, making existing hardware accessible to anyone who needs it.

## 2. Goals

- Provider can register a node.
- Client can submit inference requests.
- Inference requests can be executed on provider's GPU; if the requested model by the client is not on the provider's machine, it will install it.
- Return inference results to the client.

## 3. Non-Goals

- Payments
- Multi-GPU support
- Private models
- Training
- Fine-tuning

## 4. Terminology

### Provider
A user who contributes GPU compute to the network.

### Client
A user or application that submits inference requests.

### Node
The software running on a provider's machine.

### Scheduler
The component responsible for assigning inference jobs to nodes.

## 5. System Overview
+----------------+
|    Client      |
+-------+--------+
        |
    HTTP/HTTPS
        |
+-------v--------+
| Gateway/API    |
| FastAPI        |
+-------+--------+
        |
Select provider
        |
+-------v--------+
| Provider Node  |
| FastAPI        |
| llama.cpp      |
+----------------+

## 6. Functional Requirements

### FR-001 - Provider Registration
A provider shall be able to register a node with the gateway.

The registration request shall include:

- Node ID
- GPU model
- Available VRAM
- Maximum GPU utilization
- Availability schedule

---

### FR-002 - Heartbeat
Each node shall periodically send a heartbeat to the gateway.

If a node does not send a heartbeat within the configured timeout, it shall be considered offline.

---

### FR-003 - Model Management
When a node receives an inference request:

- If the model is already installed, it shall be loaded.
- Otherwise, the node shall download the model before executing the request.

---

### FR-004 - Inference
Clients shall be able to submit inference requests.

The request shall contain:

- Model
- Prompt
- Generation parameters

The gateway shall forward the request to an available provider.

---

### FR-005 - Response
The generated response shall be returned to the client.


## 7. Non-Functional Requirements

### Performance
The system should minimise inference latency.

### Availability
Offline providers shall not receive inference requests.

### Scalability
The architecture should support adding additional providers without modifying existing nodes.

### Reliability
Inference requests shall either complete successfully or return an explicit error.

### Security
All communication shall use HTTPS.

## 8. Architecture
The MVP consists of two services.

### Gateway
Responsibilities:

- Register providers.
- Receive inference requests.
- Select an available provider.
- Forward requests.

### Provider Node
Responsibilities:

- Register with the gateway.
- Download models.
- Execute inference.
- Return results.

## 9. Components

| Component     | Description                 |
| ------------- | --------------------------- |
| Gateway       | Central API                 |
| Provider Node | Executes inference          |
| llama.cpp     | Inference engine            |
| PostgreSQL    | Stores provider information |

## 10. API

POST /providers/register

POST /providers/heartbeat

POST /inference

GET /models

## 11. Data Model

Client
- id
- first_name
- last_name

Provider

- id
- gpu_name
- vram
- max_gpu_usage
- availability
- status

InferenceJob

- id
- client_id
- provider_id
- model
- prompt
- state

## 12. Job Lifecycle

Client

↓

POST /inference

↓

Gateway

↓

Select Provider

↓

Provider Node

↓

Download Model (if needed)

↓

Run Inference

↓

Return Response

## 13. Security

- HTTPS only.
- Providers authenticate using API keys.
- Clients authenticate using API keys.
- Only approved open-source models may be executed.

## 14. Roadmap

v0.1

- Single gateway
- Single provider
- Remote inference

v0.2

- Multiple providers
- Scheduler
- Dashboard

v0.3

- Desktop application

v0.4

- Payments

## 15. Assumptions

- Only open-source models are supported.
- Only inference is supported.
- Providers execute approved inference engines.
- Each provider runs a single node.
- Clients do not communicate directly with providers.
- The gateway is trusted.
