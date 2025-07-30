# InvOCR - Invoice OCR & Conversion System

> 🔍 Universal document processing system with OCR capabilities for invoices, receipts, and financial documents

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License: Apache](https://img.shields.io/badge/License-Apache-yellow.svg)](https://opensource.org/licenses/Apache)

## 🚀 Features

### 📄 Document Processing
- **PDF → Images** (PNG/JPG) with configurable DPI
- **Image → JSON** using advanced OCR (Tesseract + EasyOCR)
- **PDF → JSON** (direct text + OCR fallback)
- **JSON → XML** (EU Invoice standard format)
- **JSON → HTML** (responsive templates)
- **HTML → PDF** (professional output)

### 🌍 Multi-language Support
- English, Polish, German, French, Spanish, Italian
- Auto-detection of document language
- Custom language combinations

### 📋 Document Types
- ✅ **Invoices** (commercial invoices)
- ✅ **Receipts** (retail receipts)
- ✅ **Payment confirmations**
- ✅ **Financial documents**
- ✅ **Custom business documents**

### 🔧 Interfaces
- **CLI** - Command line interface
- **REST API** - Web API with OpenAPI docs
- **Docker** - Containerized deployment
- **Batch processing** - Multiple files

## 🏗️ Project Structure

```
invocr/
├── 📁 invocr/                 # Main package
│   ├── 📁 core/               # Core processing modules
│   │   ├── ocr.py            # OCR engine (Tesseract + EasyOCR)
│   │   ├── converter.py      # Universal format converter
│   │   ├── extractor.py      # Data extraction logic
│   │   └── validator.py      # Data validation
│   │
│   ├── 📁 formats/            # Format-specific handlers
│   │   ├── pdf.py           # PDF operations
│   │   ├── image.py         # Image processing
│   │   ├── json_handler.py  # JSON operations
│   │   ├── xml_handler.py   # EU XML format
│   │   └── html_handler.py  # HTML generation
│   │
│   ├── 📁 api/               # REST API
│   │   ├── main.py          # FastAPI application
│   │   ├── routes.py        # API endpoints
│   │   └── models.py        # Pydantic models
│   │
│   ├── 📁 cli/               # Command line interface
│   │   └── commands.py      # CLI commands
│   │
│   └── 📁 utils/             # Utilities
│       ├── config.py        # Configuration
│       ├── logger.py        # Logging setup
│       └── helpers.py       # Helper functions
│
├── 📁 tests/                 # Test suite
├── 📁 scripts/               # Installation scripts
├── 📁 docs/                  # Documentation
├── 🐳 Dockerfile             # Docker configuration
├── 🐳 docker-compose.yml     # Docker Compose
├── 📋 pyproject.toml         # Poetry configuration
└── 📖 README.md              # This file
```

## ⚡ Quick Start

### Option 1: Auto Installation (Recommended)

```bash
# Clone repository
git clone https://github.com/your-username/invocr.git
cd invocr

# Run installation script
chmod +x scripts/install.sh
./scripts/install.sh
```

### Option 2: Manual Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-pol poppler-utils \
    libpango-1.0-0 libharfbuzz0b python3-dev build-essential

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Python dependencies
poetry install

# Setup environment
cp .env.example .env
```

### Option 3: Docker

```bash
# Using Docker Compose (easiest)
docker-compose up

# Or build manually
docker build -t invocr .
docker run -p 8000:8000 invocr
```

## 📚 Usage Examples

### CLI Commands

```bash
# Convert PDF to JSON
invocr convert invoice.pdf invoice.json

# Convert with specific languages
invocr convert -l en,pl,de document.pdf output.json

# PDF to images
invocr pdf2img document.pdf ./images/ --format png --dpi 300

# Image to JSON (OCR)
invocr img2json scan.png data.json --doc-type invoice

# JSON to EU XML format
invocr json2xml data.json invoice.xml

# Batch processing
invocr batch ./input_files/ ./output/ --format json --parallel 4

# Full pipeline: PDF → IMG → JSON → XML → HTML → PDF
invocr pipeline document.pdf ./results/

# Start API server
invocr serve --host 0.0.0.0 --port 8000
```

### REST API

```bash
# Start server
invocr serve

# Convert file
curl -X POST "http://localhost:8000/convert" \
  -F "file=@invoice.pdf" \
  -F "target_format=json" \
  -F "languages=en,pl"

# Check job status
curl "http://localhost:8000/status/{job_id}"

# Download result
curl "http://localhost:8000/download/{job_id}" -o result.json
```

### Python API

```python
from invocr import create_converter

# Create converter instance
converter = create_converter(languages=['en', 'pl', 'de'])

# Convert PDF to JSON
result = converter.pdf_to_json('invoice.pdf')
print(result)

# Convert image to JSON with OCR
data = converter.image_to_json('scan.png', document_type='invoice')

# Convert JSON to EU XML
xml_content = converter.json_to_xml(data, format='eu_invoice')

# Full conversion pipeline
result = converter.convert('input.pdf', 'output.json', 'auto', 'json')
```

## 🌐 API Documentation

When running the API server, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

- `POST /convert` - Convert single file
- `POST /convert/pdf2img` - PDF to images
- `POST /convert/img2json` - Image OCR to JSON
- `POST /batch/convert` - Batch processing
- `GET /status/{job_id}` - Job status
- `GET /download/{job_id}` - Download result
- `GET /health` - Health check
- `GET /info` - System information

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# OCR Settings
DEFAULT_OCR_ENGINE=auto          # tesseract, easyocr, auto
DEFAULT_LANGUAGES=en,pl,de,fr,es # Supported languages
OCR_CONFIDENCE_THRESHOLD=0.3     # Minimum confidence

# Processing
MAX_FILE_SIZE=52428800          # 50MB limit
PARALLEL_WORKERS=4              # Concurrent processing
MAX_PAGES_PER_PDF=10           # Page limit

# Storage
UPLOAD_DIR=./uploads
OUTPUT_DIR=./output
TEMP_DIR=./temp
```

### Supported Languages

| Code | Language | Tesseract | EasyOCR |
|------|----------|-----------|---------|
| `en` | English | ✅ | ✅ |
| `pl` | Polish | ✅ | ✅ |
| `de` | German | ✅ | ✅ |
| `fr` | French | ✅ | ✅ |
| `es` | Spanish | ✅ | ✅ |
| `it` | Italian | ✅ | ✅ |

## 📊 Supported Formats

### Input Formats
- **PDF** (.pdf)
- **Images** (.png, .jpg, .jpeg, .tiff, .bmp)
- **JSON** (.json)
- **XML** (.xml)
- **HTML** (.html)

### Output Formats
- **JSON** - Structured data
- **XML** - EU Invoice standard
- **HTML** - Responsive templates
- **PDF** - Professional documents

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=invocr

# Run specific test file
poetry run pytest tests/test_ocr.py

# Run API tests
poetry run pytest tests/test_api.py
```

## 🚀 Deployment

### Production with Docker

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  invocr:
    image: invocr:latest
    ports:
      - "80:8000"
    environment:
      - ENVIRONMENT=production
      - WORKERS=4
    volumes:
      - ./data:/app/data
```

### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: invocr
spec:
  replicas: 3
  selector:
    matchLabels:
      app: invocr
  template:
    metadata:
      labels:
        app: invocr
    spec:
      containers:
      - name: invocr
        image: invocr:latest
        ports:
        - containerPort: 8000
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes
4. Add tests
5. Run tests (`poetry run pytest`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

### Development Setup

```bash
# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Run linting
poetry run black invocr/
poetry run isort invocr/
poetry run flake8 invocr/

# Run type checking
poetry run mypy invocr/
```

## 📈 Performance

### Benchmarks

| Operation | Time | Memory |
|-----------|------|--------|
| PDF → JSON (1 page) | ~2-3s | ~50MB |
| Image OCR → JSON | ~1-2s | ~30MB |
| JSON → XML | ~0.1s | ~10MB |
| JSON → HTML | ~0.2s | ~15MB |
| HTML → PDF | ~1-2s | ~40MB |

### Optimization Tips

- Use `--parallel` for batch processing
- Enable `IMAGE_ENHANCEMENT=false` for faster OCR
- Use `tesseract` engine for better performance
- Configure `MAX_PAGES_PER_PDF` for large documents

## 🔒 Security

- File upload validation
- Size limits enforced
- Input sanitization
- No execution of uploaded content
- Rate limiting available
- CORS configuration

## 📋 Requirements

### System Requirements
- **Python**: 3.9+
- **Memory**: 1GB+ RAM
- **Storage**: 500MB+ free space
- **OS**: Linux, macOS, Windows (Docker)

### Dependencies
- **Tesseract OCR**: Text recognition
- **EasyOCR**: Neural OCR engine
- **WeasyPrint**: HTML to PDF conversion
- **FastAPI**: Web framework
- **Pydantic**: Data validation

## 🐛 Troubleshooting

### Common Issues

**OCR not working:**
```bash
# Check Tesseract installation
tesseract --version

# Install missing languages
sudo apt install tesseract-ocr-pol
```

**WeasyPrint errors:**
```bash
# Install system dependencies
sudo apt install libpango-1.0-0 libharfbuzz0b
```

**Import errors:**
```bash
# Reinstall dependencies
poetry install --force
```

**Permission errors:**
```bash
# Fix file permissions
chmod -R 755 uploads/ output/
```

## 📞 Support

- 📧 **Email**: support@invocr.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/invocr/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/invocr/discussions)
- 📚 **Wiki**: [Project Wiki](https://github.com/your-username/invocr/wiki)

## 📄 License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - Neural OCR
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [WeasyPrint](https://weasyprint.org/) - HTML/CSS to PDF
- [Poetry](https://python-poetry.org/) - Dependency management

---

**Made with ❤️ for the open source community**

⭐ **Star this repository if you find it useful!**








# ---

# scripts/setup_env.py
#!/usr/bin/env python3
"""
Environment setup script for InvOCR
Configures environment variables and validates setup
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment variables and directories"""
    print("🔧 Setting up InvOCR environment...")
    
    # Project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Create directories
    directories = ["uploads", "output", "temp", "logs", "static"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Setup environment file
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
    elif not env_file.exists():
        # Create basic .env file
        create_basic_env_file(env_file)
        print("✅ Created basic .env file")
    
    # Validate setup
    validate_setup()
    
    print("🎉 Environment setup completed!")

def create_basic_env_file(env_path: Path):
    """Create basic environment file"""
    content = """# InvOCR Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Storage
UPLOAD_DIR=./uploads
OUTPUT_DIR=./output
TEMP_DIR=./temp
LOGS_DIR=./logs

# OCR
DEFAULT_LANGUAGES=en,pl,de,fr,es,it
OCR_CONFIDENCE_THRESHOLD=0.3

# Processing
MAX_FILE_SIZE=52428800
PARALLEL_WORKERS=4

# Security
SECRET_KEY=change-me-in-production
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)

def validate_setup():
    """Validate environment setup"""
    print("🔍 Validating setup...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check directories
    required_dirs = ["uploads", "output", "temp", "logs"]
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Missing directory: {directory}")
    
    # Check environment file
    if Path(".env").exists():
        print("✅ Environment file exists")
    else:
        print("❌ Missing .env file")
    
    # Try importing invocr
    try:
        import invocr
        print("✅ InvOCR package importable")
    except ImportError as e:
        print(f"❌ Cannot import InvOCR: {e}")
        print("Run: poetry install")
    
    return True

if __name__ == "__main__":
    setup_environment()

# ---

# docs/api.md
# InvOCR API Documentation

## Overview

The InvOCR REST API provides endpoints for document conversion and OCR processing.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required for local development.

## Endpoints

### Health Check

```http
GET /health
```

Returns system health status.

### System Information

```http
GET /info
```

Returns supported formats, languages, and features.

### Convert File

```http
POST /convert
```

Convert uploaded file to specified format.

**Parameters:**
- `file` (file): Input file
- `target_format` (string): Output format (json, xml, html, pdf)
- `languages` (string): Comma-separated language codes
- `async_processing` (boolean): Process in background

### Check Job Status

```http
GET /status/{job_id}
```

Get conversion job status.

### Download Result

```http
GET /download/{job_id}
```

Download conversion result.

## Example Usage

```bash
# Convert PDF to JSON
curl -X POST "http://localhost:8000/convert" \
  -F "file=@invoice.pdf" \
  -F "target_format=json"

# Check status
curl "http://localhost:8000/status/job-id"

# Download result
curl "http://localhost:8000/download/job-id" -o result.json
```

# ---

# docs/cli.md
# InvOCR CLI Documentation

## Installation

```bash
poetry install
```

## Usage

### Basic Commands

```bash
# Show help
invocr --help

# Convert single file
invocr convert input.pdf output.json

# Convert with specific languages
invocr convert -l en,pl,de document.pdf output.json

# Convert PDF to images
invocr pdf2img document.pdf ./images/

# Image to JSON (OCR)
invocr img2json scan.png data.json

# JSON to XML
invocr json2xml data.json invoice.xml

# Batch processing
invocr batch ./pdfs/ ./output/ --format json

# Full pipeline
invocr pipeline document.pdf ./results/

# Start API server
invocr serve
```

### Advanced Options

```bash
# Batch processing with parallelization
invocr batch ./input/ ./output/ --parallel 8 --format xml

# Custom OCR languages
invocr img2json scan.png data.json --languages en,pl,de,fr

# Custom templates
invocr convert data.json invoice.html --template classic

# API server with custom host/port
invocr serve --host 0.0.0.0 --port 9000
```

### Examples

```bash
# Convert invoice PDF to JSON
invocr convert invoice.pdf invoice.json

# Process receipt image
invocr img2json receipt.jpg receipt.json --doc-type receipt

# Generate EU standard XML
invocr json2xml invoice.json eu_invoice.xml

# Create HTML invoice
invocr json2html invoice.json invoice.html --template modern
```