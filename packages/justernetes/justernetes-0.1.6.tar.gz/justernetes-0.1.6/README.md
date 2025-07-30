# Justernetes

Justernetes is a Kubernetes operator designed to manage and orchestrate Justniffer-powered network monitoring pipelines via Custom Resource Definitions (CRDs). It automates lifecycle operations (create, update, delete), ensures runtime consistency across distributed environments, and integrates seamlessly with a Justniffer proxy API.

## Features

- 🌀 Declarative control of network sniffing configurations through CRDs
- ⚙️ Automated lifecycle reconciliation with status tracking
- 🔁 Debounced sync for efficient resource alignment
- 🔍 Runtime validation of active Justniffer processes
- 📦 Pydantic-powered schema validation

## CRD Overview

Each `Justniffer` custom resource includes:

- Target network interface
- Optional filters and log formatting
- Runtime control flags (e.g., truncation, encoding, activation)
- Status and condition tracking with lifecycle phase updates

## Getting Started

1. **Deploy the Operator**
   ```bash
   kubectl apply -f deploy/operator.yaml
