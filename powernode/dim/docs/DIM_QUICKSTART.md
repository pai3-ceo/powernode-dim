# DIM Quickstart

**For**: AI Testing Agent (Devin.AI, etc.)  
**Purpose**: Quick reference for immediate test execution

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Verify Prerequisites
```bash
python3 --version  # Must be 3.11+
node --version     # Must be 20+
ipfs --version     # Must be installed
```

### Step 2: Install Dependencies
```bash
cd powernode/dim
pip install -r orchestrator/requirements.txt
pip install -r daemon/requirements.txt
pip install -r tests/requirements.txt
cd api-gateway && npm install && cd ..
```

### Step 3: Start IPFS
```bash
ipfs daemon &
sleep 5
ipfs id  # Verify running
```

### Step 4: Run Tests
```bash
# All tests
pytest tests/ -v --cov=powernode.dim --cov-report=html

# Or by category
pytest tests/unit/ -v -m unit
pytest tests/integration/ -v -m integration
```

---

## 📋 Test Execution Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] IPFS installed and running
- [ ] Dependencies installed
- [ ] IPFS daemon started
- [ ] Configuration verified (`config/dev.yaml`)
- [ ] Unit tests run successfully
- [ ] Integration tests run successfully
- [ ] Coverage report generated

---

## 🎯 Critical Test Areas

1. **Orchestrator**: Job submission, status, cancellation
2. **Daemon**: Job execution, resource management
3. **IPFS**: State management, Pubsub, IPNS
4. **Pattern Engines**: All three patterns work
5. **gRPC**: Services start and respond
6. **Node Discovery**: Registration and discovery
7. **Performance**: Optimizations work
8. **Security**: Rate limiting, TLS

---

## 📊 Expected Results

- **Unit Tests**: 80%+ pass rate, 80%+ coverage
- **Integration Tests**: 100% pass rate
- **E2E Tests**: All workflows complete
- **Performance**: Meets requirements
- **Security**: All features validated

---

## 🔍 Key Files

- **Main Code**: `orchestrator/src/`, `daemon/src/`
- **Tests**: `tests/`
- **Config**: `config/dev.yaml`
- **Docs**: `docs/TEST_PLAN.md`, `docs/TEST_CASES.md`

---

## ⚠️ Common Issues

1. **IPFS not running**: `ipfs daemon &`
2. **Import errors**: Set PYTHONPATH
3. **Port conflicts**: Update `config/dev.yaml`
4. **Missing deps**: Run setup scripts

---

**For detailed information, see**: `docs/DIM_TESTING_SCOPE.md`

