# Oscillo-evaluator

**oscillo-evaluator** is a Python application for evaluating oscilloscope signal data. It analyze waveform outputs, extract features and bulk results to Elasticsearch.

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
