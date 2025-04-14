# Oscillo-evaluator

**oscillo-evaluator** is a Python application for evaluating oscilloscope signal data. It helps analyze waveform outputs, extract features, and optionally visualize signal behavior using a configurable and scriptable backend.

---

## 🧰 Features

- 📊 Evaluate and process oscilloscope signals
- ⚙️ Flexible processing logic (e.g., window splitting, time analysis)
- 📂 Easy configuration via environment or CLI
- 🐍 Async-compatible for fast integrations (e.g., querying Elasticsearch)
- 🧪 Built-in test suite using `pytest`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip
- (Optional) Docker

### Clone the Repository

```bash
git clone https://github.com/matusravas/oscillo-evaluator.git
cd oscillo-evaluator
```

# Installation

```
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

# Configuration

```
ES_HOSTS=localhost:9200,localhost:9201
ES_TOKEN=your-secret-token
```
