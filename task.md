# Project Tasks: Cognitive Edge-Orchestrated IBN

## Phase 1: Setup & Infrastructure
- [ ] Environment Setup <!-- id: 1 -->
    - [ ] Configure Raspberry Pi / Development Environment (Docker, Python dependencies)
    - [ ] Install System Tools (`tc`, `iproute2`, `iptables`)
- [ ] Middleware Deployment <!-- id: 2 -->
    - [ ] Setup MQTT Broker (Mosquitto)
    - [ ] Deploy Prometheus (Metrics Collection)
    - [ ] Deploy Grafana (Visualization)

## Phase 2: Core Framework Development
- [ ] Intent Management <!-- id: 3 -->
    - [ ] Implement Intent Acquisition Interface (REST API / Web UI)
    - [ ] Develop Rule-Based Intent Parser (Structured/Natural Language to Parameters)
- [ ] Policy Engine <!-- id: 4 -->
    - [ ] Design Policy Internal Representation
    - [ ] Implement Policy Generation Logic (Map Intents -> Traffic/Device Rules)
- [ ] Enforcement Module <!-- id: 5 -->
    - [ ] Implement Network Enforcement Wrapper (`tc`, `netem` calls)
    - [ ] Implement Device Enforcement Wrapper (MQTT Publish)

## Phase 3: IoT & Adaptation
- [ ] IoT Node Simulation <!-- id: 6 -->
    - [ ] Create Dockerized IoT Node Simulator (Traffic Generator)
    - [ ] Implement MQTT Subscriber/Publisher on Nodes
- [ ] Feedback Loop <!-- id: 7 -->
    - [ ] Implement Metric Exporters (Latency, Throughput)
    - [ ] Develop Feedback Engine (Compare Metrics vs. Intent Goals)
    - [ ] Implement Self-Correction Logic

## Phase 4: Integration & Verification
- [ ] Visualization <!-- id: 8 -->
    - [ ] Design Grafana Dashboards
- [ ] System Validation <!-- id: 9 -->
    - [ ] Verify Intent-to-Policy Accuracy
    - [ ] Verify Real-Time Enforcement (Latency/Throughput tests)
    - [ ] Verify Feedback Loop Stability

## Completed Tasks
- [x] Analyze Requirements and Existing README <!-- id: 0 -->
- [x] Create Implementation Plan <!-- id: 10 -->
- [x] Rewrite README.md <!-- id: 11 -->
