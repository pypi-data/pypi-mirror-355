# UnifyDoc

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/unifydoc.svg)](https://badge.fury.io/py/unifydoc)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**UnifyDoc** is a powerful AI-powered document processing library that unifies the handling of multiple document formats with advanced OCR capabilities. It provides language-agnostic text extraction, comprehensive configuration options, and intelligent batch processing.

## 🎯 Perfect for LLM RAG Pipelines - Complex Table Extraction

UnifyDoc is specifically designed to solve one of the biggest challenges in RAG pipelines: **extracting and preserving complex table structures** from diverse document formats. 

### 🏆 Why UnifyDoc for Table-Heavy Documents?

Traditional document loaders often fail with:
- ❌ **Merged cells** in Excel spreadsheets become jumbled text
- ❌ **Multi-level headers** lose their hierarchical relationships  
- ❌ **Scanned PDF tables** are completely ignored or garbled
- ❌ **Cross-references** between sheets/tables are lost

UnifyDoc solves all these problems:

### ✅ Real-World Example: Complex Financial Tables with Merged Cells

```python
from unifydoc import UnifiedDocumentLoader

# Initialize with table-focused extraction
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    prompt_template='table_focused',  # Specialized for complex tables
    model='gpt-4-vision-preview',
    instructions="Preserve all merged cells, maintain hierarchical headers, and capture formulas"
)

# Extract from Excel with complex merged cells and multiple sheets
result = loader.load('sample_documents/sample_spreadsheet.xlsx', output_format='markdown')

# UnifyDoc preserves the EXACT structure, even with merged cells:
print(result.content)
```

**Output preserves complex structures:**
```markdown
## Sheet: Financial Summary

| Department      | Q1 2024        | Q2 2024        | H1 Total       |
|                 | Revenue | Cost | Revenue | Cost | Revenue | Cost |
|-----------------|---------|------|---------|------|---------|------|
| **Sales**       |         |      |         |      |         |      |
| - North Region  | 125.5   | 45.2 | 142.3   | 48.7 | 267.8   | 93.9 |
| - South Region  | 89.2    | 32.1 | 95.1    | 35.2 | 184.3   | 67.3 |
| **Marketing**   | 156.7   | 89.3 | 178.4   | 95.6 | 335.1   | 184.9|
| **TOTAL**       | 371.4   | 166.6| 415.8   | 179.5| 787.2   | 346.1|
```

### 🔥 Advanced Table Processing Features

```python
# Handle scanned PDFs with table detection
result = loader.load('scanned_report.pdf', 
    extract_images=True,
    ocr_images=True,
    instructions="Focus on detecting table boundaries and maintaining cell alignment"
)

# Extract only tables from mixed documents
json_result = loader.load('report.docx', output_format='json')
import json
data = json.loads(json_result.content)

# Filter and process only table content
tables = [item for item in data['content'] if item['type'] == 'table']
for idx, table in enumerate(tables):
    print(f"Table {idx + 1}: {table['content'][:100]}...")
    # Each table is perfectly structured for vector database indexing
```

### 📈 Comparison: UnifyDoc vs Traditional Document Loaders

| Feature | UnifyDoc | Traditional Loaders |
|---------|----------|-------------------|
| **Merged Cells** | ✅ Perfectly preserved | ❌ Lost or jumbled |
| **Multi-level Headers** | ✅ Maintains hierarchy | ❌ Flattened |
| **Cross-sheet References** | ✅ Tracked & maintained | ❌ Ignored |
| **Scanned Table OCR** | ✅ AI-powered extraction | ❌ Skipped |
| **Table Formulas** | ✅ Captured in metadata | ❌ Lost |
| **Complex Layouts** | ✅ Structure preserved | ❌ Linearized |
| **Output Formats** | ✅ Markdown, JSON, Text | ⚠️ Limited |

## 🚀 Key Features

- **Universal Document Support**: Process PDF, DOCX, XLSX, PPTX, TXT, CSV, JSON, HTML, Markdown, and legacy formats
- **AI-Powered OCR**: Advanced GPT-4V-based OCR with language-agnostic prompts
- **Multiple Prompt Templates**: Specialized prompts for tables, documents, forms, receipts, handwriting, and code
- **Efficient Batch Processing**: LangChain-powered batch OCR with automatic fallbacks
- **Language Preservation**: Maintains original language and formatting without translation bias
- **Comprehensive Configuration**: Full control over model parameters, workers, timeouts, and retry logic
- **Smart Format Detection**: Automatic format detection and appropriate processor selection
- **Rich Output Formats**: Generate clean Markdown, structured JSON, or raw text

## 📦 Installation

### Basic Installation

```bash
pip install unifydoc
```

### With OCR Support

```bash
pip install unifydoc[ocr]
# or
pip install unifydoc openai langchain-openai
```

### With All Features

```bash
pip install unifydoc[all]
```

## 🔧 Quick Start

### Simple Usage

```python
from unifydoc import UnifiedDocumentLoader

# Initialize loader
loader = UnifiedDocumentLoader()  # Uses OpenAI by default

# Load a document
result = loader.load('document.pdf')
print(result.content)  # Extracted text in Markdown format
```

### Basic Usage with Parameters

```python
from unifydoc import UnifiedDocumentLoader
from unifydoc.core.base import OutputFormat

# Initialize with specific OCR provider
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    api_key='your-openai-api-key'  # or set OPENAI_API_KEY env var
)

# Load document with options
result = loader.load(
    'document.pdf',
    output_format=OutputFormat.MARKDOWN,  # Output format
    extract_images=True,                  # Extract images
    ocr_images=True                       # Apply OCR to images
)

print(result.content)  # Extracted content
print(result.metadata)  # Document metadata
print(result.images)   # Extracted images (if any)
```

### Environment Setup

```bash
# Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

## 📋 Parameter Reference

### UnifiedDocumentLoader Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Core Parameters** | | | |
| `ocr_provider` | str/OCRProvider/BaseOCR | 'openai' | OCR provider: 'openai', 'tesseract', or custom instance |
| `api_key` | str | None | API key for OCR provider (uses OPENAI_API_KEY env var if not provided) |
| `ocr_config` | OCRConfig | None | OCR configuration object with language and processing settings |
| `cache_dir` | str | None | Directory for caching processed documents |
| **OpenAI OCR Parameters** | | | |
| `model` | str | 'gpt-4.1' | OpenAI model to use for OCR |
| `temperature` | float | 0 | Temperature for text generation (0.0-2.0, lower = more deterministic) |
| `max_tokens` | int | 4096 | Maximum tokens in OCR response (1-4096) |
| `max_workers` | int | 5 | Maximum concurrent workers for batch processing |
| `prompt_template` | str/PromptTemplate | PromptTemplate.DEFAULT | OCR prompt template to use |
| `timeout` | int | 30 | Request timeout in seconds |
| `max_retries` | int | 3 | Maximum number of retries for failed requests |
| `top_p` | float | 1.0 | Nucleus sampling parameter (0.0-1.0) |
| `frequency_penalty` | float | 0.0 | Reduce word repetition (-2.0 to 2.0) |
| `presence_penalty` | float | 0.0 | Encourage new topics (-2.0 to 2.0) |
| `default_prompt` | str | None | Custom default prompt to override built-in templates |
| **Tesseract Parameters** | | | |
| `tesseract_lang` | str | 'eng' | Language code for Tesseract ('eng', 'chi_sim', 'jpn', etc.) |
| `tesseract_config` | str | '--psm 3 --oem 3' | Tesseract configuration string |

#### Language Configuration

```python
from unifydoc.ocr.base import OCRConfig

# Configure OCR with specific language
ocr_config = OCRConfig(
    language='chinese',  # Specify expected language
    enhance_image=True,  # Enable image preprocessing
    detect_tables=True,  # Enable table detection
    detect_layout=True   # Enable layout analysis
)

loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    ocr_config=ocr_config
)
```

### load() Method Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Required Parameters** | | | |
| `file_path` | str/Path | Required | Path to the document file |
| **Output Control** | | | |
| `output_format` | OutputFormat/str | OutputFormat.MARKDOWN | Output format: 'markdown', 'json', 'text' |
| `extract_images` | bool | False | Extract images as base64 data |
| `ocr_images` | bool | False | Apply OCR to extracted images (requires extract_images=True) |
| `preserve_layout` | bool | True | Preserve document structure and formatting |
| `show_progress` | bool | False | Display progress messages during processing |
| **OCR Parameters (per-load)** | | | |
| `language` | str | None | Language hint for OCR (e.g., 'English', 'Chinese', 'Spanish') |
| `content_type` | str | None | Content type hint: 'table', 'form', 'receipt', 'document', 'handwriting', 'code' |
| `instructions` | str | None | Custom OCR instructions that completely replace ALL prompts (highest priority) |
| `prompt_template_override` | str/PromptTemplate | None | Switch to a different built-in template for this load (ignored if instructions is set) |
| **Image Saving Options** | | | |
| `save_images_locally` | bool | False | Save images to disk instead of base64 encoding |
| `local_image_dir` | str | './images' | Directory to save images when save_images_locally=True |
| **Performance Parameters** | | | |
| `batch_size` | int | None | Batch size for processing multiple images (auto-determined if None) |
| **Format-Specific Parameters** | | | |
| `encoding` | str | 'utf-8' | Text encoding for text files |
| `delimiter` | str | None | Delimiter for CSV files (auto-detect if None) |

### Enum Values

#### OutputFormat
```python
from unifydoc.core.base import OutputFormat

# Available output formats
OutputFormat.MARKDOWN  # Formatted markdown text (default)
OutputFormat.JSON      # Structured JSON with content and metadata
OutputFormat.TEXT      # Plain text without formatting
```

#### OCRProvider
```python
from unifydoc.ocr.base import OCRProvider

# Available OCR providers
OCRProvider.OPENAI     # OpenAI GPT-4V (requires API key)
OCRProvider.TESSERACT  # Tesseract OCR (offline, free)
```

#### PromptTemplate
```python
from unifydoc.ocr.prompts import PromptTemplate

# Available prompt templates for OCR
PromptTemplate.DEFAULT              # General-purpose OCR
PromptTemplate.TABLE_FOCUSED        # Optimized for tables
PromptTemplate.DOCUMENT_FOCUSED     # Preserves document structure
PromptTemplate.MULTILINGUAL         # Enhanced multilingual support
PromptTemplate.FORM_FOCUSED         # Form field extraction
PromptTemplate.RECEIPT_FOCUSED      # Receipt/invoice processing
PromptTemplate.HANDWRITING_FOCUSED  # Handwritten text
PromptTemplate.CODE_FOCUSED         # Source code and technical docs
```

### Usage Examples

#### Extract Images with OCR
```python
# Extract and OCR all images in a document
result = loader.load(
    'report.pdf',
    extract_images=True,
    ocr_images=True,
    output_format=OutputFormat.MARKDOWN
)

# OCR results are embedded as <image_ocr_result>...</image_ocr_result>
```

#### JSON Output Format
```python
# Get structured JSON output
result = loader.load(
    'document.docx',
    output_format=OutputFormat.JSON
)

# Parse the JSON content
import json
data = json.loads(result.content)
print(data['content'])  # List of content items
print(data['metadata'])  # Document metadata
```

#### Plain Text Output
```python
# Get plain text without formatting
result = loader.load(
    'document.pdf',
    output_format=OutputFormat.TEXT
)

# Clean text suitable for NLP processing
print(result.content)
```

### 🤖 RAG Pipeline Integration

UnifyDoc is designed to seamlessly integrate with popular RAG frameworks and vector databases:

#### 📊 Table-Specific RAG Use Cases

**1. Financial Analysis Q&A**
```python
# Extract quarterly reports with complex tables
loader = UnifiedDocumentLoader(prompt_template='table_focused')
quarters = ['Q1_report.xlsx', 'Q2_report.xlsx', 'Q3_report.xlsx', 'Q4_report.xlsx']

# Build knowledge base from tables
knowledge_base = []
for report in quarters:
    result = loader.load(report, output_format='json')
    data = json.loads(result.content)
    # Each table maintains its structure for accurate Q&A
    knowledge_base.extend([item for item in data['content'] if item['type'] == 'table'])

# Now you can answer: "What was the revenue growth from Q1 to Q4?"
# The preserved table structure ensures accurate data retrieval
```

**2. Cross-Document Table Comparison**
```python
# Compare product specifications across different vendor documents
vendors = ['vendor_a.pdf', 'vendor_b.docx', 'vendor_c.xlsx']
specs = {}

for vendor_doc in vendors:
    result = loader.load(vendor_doc, output_format='markdown')
    # Tables maintain headers and structure for accurate comparison
    specs[vendor_doc] = result.content

# Perfect for: "Compare the pricing tiers across all vendors"
```

**3. Regulatory Compliance Checking**
```python
# Extract tables from compliance documents
compliance_docs = ['regulations.pdf', 'requirements.xlsx', 'standards.docx']

for doc in compliance_docs:
    result = loader.load(doc, 
        extract_images=True,  # Capture scanned tables
        ocr_images=True,
        instructions="Extract all tables, requirements lists, and compliance matrices"
    )
    # Structured extraction ensures no compliance data is missed
```

#### LangChain Integration
```python
from unifydoc import UnifiedDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# Extract tables from multiple documents
loader = UnifiedDocumentLoader(prompt_template='table_focused')
documents = ['report.xlsx', 'data.pdf', 'analysis.docx']

# Process and prepare for RAG
all_content = []
for doc in documents:
    result = loader.load(doc, output_format='markdown')
    all_content.append({
        'content': result.content,
        'source': doc,
        'metadata': result.metadata
    })

# Split and embed for vector database
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
embeddings = OpenAIEmbeddings()

# Store in vector database
texts = [doc['content'] for doc in all_content]
metadatas = [{'source': doc['source']} for doc in all_content]
vectorstore = Chroma.from_texts(texts, embeddings, metadatas=metadatas)
```

#### Table-Specific RAG Queries
```python
# Extract only tables for structured Q&A
result = loader.load('financial_report.xlsx', output_format='json')
data = json.loads(result.content)

# Filter table content
tables = [item for item in data['content'] if item['type'] == 'table']

# Now you can:
# - Query specific metrics across tables
# - Compare data between different time periods
# - Generate insights from tabular data
# - Answer complex analytical questions
```

### Advanced Usage Examples

#### Full Control Example
```python
from unifydoc import UnifiedDocumentLoader
from unifydoc.core.base import OutputFormat
from unifydoc.ocr.base import OCRConfig
from unifydoc.ocr.prompts import PromptTemplate

# Initialize with complete configuration
loader = UnifiedDocumentLoader(
    # OCR Provider Configuration
    ocr_provider='openai',
    api_key='your-api-key',
    
    # OCR Configuration
    ocr_config=OCRConfig(
        language='chinese',
        enhance_image=True,
        detect_tables=True,
        detect_layout=True
    ),
    
    # OpenAI Model Configuration
    model='gpt-4.1',
    temperature=0.1,
    max_tokens=4096,
    max_workers=8,
    prompt_template=PromptTemplate.TABLE_FOCUSED,
    timeout=60,
    max_retries=5,
    
    # Advanced OpenAI Parameters
    top_p=0.95,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    
    # Custom prompt override
    default_prompt="Extract all text maintaining exact formatting..."
)

# Load with all parameters exposed
result = loader.load(
    'complex_document.pdf',
    
    # Output Control
    output_format=OutputFormat.MARKDOWN,
    extract_images=True,
    ocr_images=True,
    preserve_layout=True,
    show_progress=True,
    
    # OCR Parameters for this specific load
    language='Chinese',
    content_type='table',
    instructions="Focus on extracting tabular data with high precision",
    prompt_template_override=PromptTemplate.TABLE_FOCUSED,
    
    # Image Handling
    save_images_locally=False,
    local_image_dir='./extracted_images',
    
    # Performance
    batch_size=10
)
```

#### Language-Specific OCR
```python
# Japanese document with specific configuration
result = loader.load(
    'japanese_report.pdf',
    extract_images=True,
    ocr_images=True,
    language='Japanese',
    content_type='document',
    prompt_template_override=PromptTemplate.MULTILINGUAL,
    show_progress=True
)
```

#### Form Processing with Custom Instructions
```python
# Process a form with specific instructions
result = loader.load(
    'application_form.pdf',
    extract_images=True,
    ocr_images=True,
    content_type='form',
    instructions="""
    Extract all form fields and their values.
    Pay special attention to:
    1. Checkbox states (checked/unchecked)
    2. Handwritten entries
    3. Signature fields
    4. Date fields
    Format as field_name: value pairs.
    """,
    output_format=OutputFormat.JSON
)
```

#### Batch Processing with Performance Tuning
```python
# Process large documents with optimized settings
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    max_workers=10,  # Increase concurrent processing
    timeout=120,     # Longer timeout for large files
    max_retries=5    # More retries for reliability
)

result = loader.load(
    'large_document.pdf',
    extract_images=True,
    ocr_images=True,
    batch_size=20,  # Process 20 images at a time
    show_progress=True
)
```

#### Save Images Locally
```python
# Extract images and save to disk instead of base64
result = loader.load(
    'document_with_images.pdf',
    extract_images=True,
    ocr_images=True,
    save_images_locally=True,
    local_image_dir='./extracted/images',
    show_progress=True
)

# Images are saved to disk and referenced in the output
```

#### CSV/Excel Processing
```python
# Process CSV with specific encoding and delimiter
result = loader.load(
    'data.csv',
    encoding='utf-8',
    delimiter=',',
    output_format=OutputFormat.JSON
)

# Process Excel files
result = loader.load(
    'report.xlsx',
    extract_images=True,  # Extract embedded charts/images
    ocr_images=True
)
```

## 📄 Supported Document Formats

### DocumentFormat Enum
```python
from unifydoc.core.base import DocumentFormat

# Modern Office Formats
DocumentFormat.DOCX    # Word documents
DocumentFormat.XLSX    # Excel spreadsheets
DocumentFormat.PPTX    # PowerPoint presentations

# Legacy Office Formats
DocumentFormat.DOC     # Legacy Word
DocumentFormat.XLS     # Legacy Excel
DocumentFormat.PPT     # Legacy PowerPoint
DocumentFormat.RTF     # Rich Text Format
DocumentFormat.PPS     # PowerPoint Show

# PDF
DocumentFormat.PDF     # Portable Document Format

# Text/Data Formats
DocumentFormat.TXT     # Plain text
DocumentFormat.CSV     # Comma-separated values
DocumentFormat.TSV     # Tab-separated values
DocumentFormat.JSON    # JSON documents
DocumentFormat.JSONL   # JSON Lines

# Markup Formats
DocumentFormat.HTML    # HTML documents
DocumentFormat.XML     # XML documents
DocumentFormat.MARKDOWN # Markdown files
```

### Format Detection
```python
# Automatic format detection based on file extension
result = loader.load('report.xlsx')  # Automatically detects Excel format
print(f"Detected format: {result.metadata.format}")
```

## 🎯 OCR Configuration & Prompt Templates

### Understanding Prompt Templates vs Instructions

#### The Difference Between `prompt_template_override` and `instructions`

UnifyDoc provides two ways to customize OCR behavior:

1. **`prompt_template_override`**: Switches between pre-built prompt templates optimized for different content types
   - Used to select a different built-in template for a specific document
   - Only changes which template is used, not the template content itself
   - Example: `prompt_template_override=PromptTemplate.TABLE_FOCUSED`

2. **`instructions`**: Provides custom instructions that completely replace ALL prompts
   - Highest priority - when set, it overrides everything else
   - Gives you complete control over the OCR prompt
   - Useful for specialized requirements not covered by built-in templates
   - Example: `instructions="Extract only financial data and format as CSV"`

**Priority Order**:
1. `instructions` (if provided) - overrides everything
2. `prompt_template_override` (if provided) - selects a different template
3. Default prompt template set during initialization

### Understanding Prompt Templates

```python
from unifydoc.ocr.prompts import PromptTemplate
from unifydoc import UnifiedDocumentLoader

# Available templates
templates = {
    PromptTemplate.DEFAULT: "Language-agnostic general-purpose OCR",
    PromptTemplate.TABLE_FOCUSED: "Optimized for tabular data extraction", 
    PromptTemplate.DOCUMENT_FOCUSED: "Preserves document structure and hierarchy",
    PromptTemplate.MULTILINGUAL: "Enhanced multilingual text processing",
    PromptTemplate.FORM_FOCUSED: "Specialized for forms and field-value extraction",
    PromptTemplate.RECEIPT_FOCUSED: "Optimized for receipts and financial documents",
    PromptTemplate.HANDWRITING_FOCUSED: "Enhanced handwritten text recognition",
    PromptTemplate.CODE_FOCUSED: "Optimized for technical documents and source code"
}
```

### Basic OCR Configuration

```python
# Simple configuration
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    prompt_template=PromptTemplate.DEFAULT,
    model='gpt-4.1'
)
```

### Advanced OCR Configuration

```python
# Comprehensive configuration with all parameters
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    api_key='your-key',
    
    # Model configuration
    model='gpt-4.1',                    # Latest GPT-4 model
    temperature=0.1,                   # Low temperature for consistency
    max_tokens=4096,                   # Maximum response length
    
    # Batch processing configuration  
    max_workers=8,                     # Concurrent processing workers
    
    # Prompt configuration
    prompt_template=PromptTemplate.DOCUMENT_FOCUSED,
    
    # Reliability configuration
    timeout=60,                        # Request timeout in seconds
    max_retries=5,                     # Retry attempts for failed requests
    
    # Additional model parameters
    top_p=0.9,                        # Nucleus sampling parameter
    frequency_penalty=0.1             # Reduce repetition
)
```

## 📊 Processing Different Document Types

### 1. Table Processing

```python
# Configure for optimal table extraction
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    prompt_template=PromptTemplate.TABLE_FOCUSED,
    model='gpt-4.1',
    temperature=0  # Deterministic for tables
)

# Process spreadsheet or PDF with tables
result = loader.load('financial_report.xlsx')

# Result contains properly formatted markdown tables
print(result.content)
"""
| Quarter | Revenue | Profit | Growth |
|---------|---------|--------|--------|
| Q1 2024 | $2.1M   | $420K  | 15.2%  |
| Q2 2024 | $2.4M   | $480K  | 14.3%  |
"""
```

### 2. Form Processing

```python
# Configure for form field extraction
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    prompt_template=PromptTemplate.FORM_FOCUSED,
    max_tokens=2048
)

# Process form with specific options
result = loader.load(
    'application_form.pdf',
    language='English',           # Language hint
    content_type='form'          # Content type hint
)

print(result.content)
"""
# Application Form Data

**Name**: John Smith
**Email**: john.smith@email.com
**Phone**: (555) 123-4567
**Position**: Software Engineer
**Experience**: 5 years
**Availability**: Immediate
"""
```

### 3. Receipt Processing

```python
# Configure for financial document processing
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    prompt_template=PromptTemplate.RECEIPT_FOCUSED
)

result = loader.load('receipt.jpg')

print(result.content)
"""
# Receipt - Store Name

**Date**: 2024-01-15
**Time**: 14:30
**Transaction ID**: #TXN-001234

## Items
- Coffee (Large): $4.99
- Sandwich: $8.50
- Tax (8.25%): $1.11

**Total**: $14.60
**Payment**: Credit Card
"""
```

### 4. Multilingual Documents

```python
# Configure for multilingual processing
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    prompt_template=PromptTemplate.MULTILINGUAL,
    temperature=0
)

# Process document with language hint
result = loader.load(
    'chinese_document.pdf',
    language='Chinese',          # Preserves original language
    content_type='document'
)

# The result preserves the original Chinese text exactly
print(result.content)
```

## ⚙️ Dynamic Configuration

### Runtime Configuration Updates

```python
from unifydoc.ocr.openai import OpenAIOCR
from unifydoc.ocr.prompts import PromptTemplate

# Initialize OCR with basic settings
ocr = OpenAIOCR()

# Check current configuration
config = ocr.get_configuration_summary()
print(f"Current model: {config['model']}")
print(f"Current template: {config['prompt_template']}")

# Update model configuration dynamically
ocr.update_model_config(
    model='gpt-4.1',
    temperature=0.2,
    max_tokens=3000,
    top_p=0.8
)

# Update prompt template
ocr.update_prompt_template(PromptTemplate.TABLE_FOCUSED)

# Get available prompts
available_prompts = ocr.get_available_prompts()
for name, description in available_prompts.items():
    print(f"{name}: {description}")
```

### Content-Specific Processing

```python
# Process different content types with optimized settings
scenarios = [
    {
        'file': 'data_table.pdf',
        'template': PromptTemplate.TABLE_FOCUSED,
        'options': {
            'content_type': 'table',
            'language': 'English'
        }
    },
    {
        'file': 'handwritten_notes.jpg', 
        'template': PromptTemplate.HANDWRITING_FOCUSED,
        'options': {
            'content_type': 'handwriting',
            'temperature': 0.3  # Slightly more creative for handwriting
        }
    },
    {
        'file': 'source_code.png',
        'template': PromptTemplate.CODE_FOCUSED,
        'options': {
            'content_type': 'code',
            'language': 'Python'
        }
    }
]

loader = UnifiedDocumentLoader(ocr_provider='openai')

for scenario in scenarios:
    # Update template for this content type
    loader.ocr.update_prompt_template(scenario['template'])
    
    # Process with specific options
    result = loader.load(
        scenario['file'],
        **scenario['options']
    )
    
    print(f"Processed {scenario['file']}:")
    print(result.content[:200] + "...")
```

## 🚄 Batch Processing

### Efficient Batch OCR

```python
# Configure for high-throughput batch processing
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    model='gpt-4.1',
    max_workers=10,              # High concurrency
    enable_langchain=True,       # Use LangChain for efficiency
    prompt_template=PromptTemplate.DEFAULT
)

# Process multiple documents
documents = [
    'doc1.pdf', 'doc2.png', 'doc3.jpg', 
    'doc4.docx', 'doc5.xlsx'
]

results = []
for doc in documents:
    result = loader.load(doc)
    results.append(result)
    print(f"Processed {doc}: {len(result.content)} characters")

# The batch processing automatically uses:
# 1. LangChain VisionAgent for efficient OpenAI API calls
# 2. ThreadPoolExecutor as fallback
# 3. Sequential processing for small batches
```

### Custom Batch Processing with OCR

```python
from unifydoc.ocr.openai import OpenAIOCR

# Direct OCR batch processing
ocr = OpenAIOCR(
    model='gpt-4.1',
    max_workers=15,
    enable_langchain=True
)

# Process multiple images
image_files = ['img1.jpg', 'img2.png', 'img3.pdf']
image_data = []

for file_path in image_files:
    with open(file_path, 'rb') as f:
        image_data.append(f.read())

# Batch process with shared options
results = ocr.batch_process_images(
    image_data,
    prompt_template=PromptTemplate.DOCUMENT_FOCUSED,
    language='English',
    content_type='document'
)

for i, result in enumerate(results):
    print(f"Image {i+1}: {result.text[:100]}...")
```

## 📝 Output Formats & Customization

### Output Format Options

```python
from unifydoc import OutputFormat

# Process with different output formats
loader = UnifiedDocumentLoader(ocr_provider='openai')

# 1. Markdown (default) - preserves structure
result = loader.load('document.pdf', output_format=OutputFormat.MARKDOWN)
print(result.content)  # Clean markdown with headers, tables, lists

# 2. Raw text - plain text only
result = loader.load('document.pdf', output_format=OutputFormat.TEXT)
print(result.content)  # Raw extracted text

# 3. JSON - structured data
result = loader.load('document.pdf', output_format=OutputFormat.JSON)
print(result.content)  # JSON with structured content
```

### Custom Instructions

```python
# Use custom instructions for specific needs
custom_instructions = """
You are processing a legal document. Please:
1. Extract all clause numbers and titles
2. Preserve exact legal terminology
3. Maintain document structure with proper headings
4. Note any signature blocks or dates
5. Format as clean markdown with a table of contents
"""

result = loader.load(
    'legal_contract.pdf',
    instructions=custom_instructions  # Override default prompts
)
```

## 🌍 Language Support & Preservation

### Language-Agnostic Processing

```python
# Process documents in any language while preserving original text
languages = ['Chinese', 'Japanese', 'Arabic', 'Russian', 'Spanish']

for lang in languages:
    result = loader.load(
        f'document_{lang.lower()}.pdf',
        prompt_template=PromptTemplate.MULTILINGUAL,
        language=lang,  # Adds language context to prompt
        content_type='document'
    )
    
    # Original language is preserved exactly
    print(f"{lang} document processed successfully")
    print(f"Content length: {len(result.content)} characters")
```

### Mixed Language Documents

```python
# Handle documents with multiple languages
result = loader.load(
    'multilingual_report.pdf',
    prompt_template=PromptTemplate.MULTILINGUAL,
    language='Mixed (English, Chinese, Spanish)',
    content_type='document'
)

# Each language section is preserved in its original form
```

## 🔍 Error Handling & Validation

### API Key Validation

```python
from unifydoc.ocr.openai import OpenAIOCR

# Validate API key before processing
ocr = OpenAIOCR(api_key='your-api-key')

if ocr.validate_api_key():
    print("✅ API key is valid")
    # Proceed with processing
else:
    print("❌ Invalid API key")
    # Handle error appropriately
```

### Robust Error Handling

```python
from unifydoc.core.base import ProcessingError, OCRError

try:
    loader = UnifiedDocumentLoader(
        ocr_provider='openai',
        max_retries=3,           # Retry failed requests
        timeout=30               # Timeout for long requests
    )
    
    result = loader.load('challenging_document.pdf')
    
except ProcessingError as e:
    print(f"Document processing failed: {e}")
    # Handle processing errors
    
except OCRError as e:
    print(f"OCR operation failed: {e}")
    # Handle OCR-specific errors
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

### Graceful Fallbacks

```python
# Configure with automatic fallbacks
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    enable_langchain=True,      # Try LangChain first
    max_workers=5,              # Fall back to ThreadPool
    # If both fail, falls back to sequential processing
)

# The system automatically chooses the best available method:
# 1. LangChain VisionAgent (most efficient)
# 2. ThreadPoolExecutor (good parallelization)  
# 3. Sequential processing (most reliable)
```

## 🔧 Advanced Usage Examples

### Custom OCR Pipeline

```python
from unifydoc.ocr.openai import OpenAIOCR
from unifydoc.ocr.prompts import PromptTemplate, build_prompt

# Create custom OCR pipeline
class CustomDocumentProcessor:
    def __init__(self):
        self.ocr = OpenAIOCR(
            model='gpt-4.1',
            temperature=0,
            max_tokens=4096,
            max_workers=8,
            enable_langchain=True
        )
    
    def process_financial_document(self, image_data):
        """Process financial documents with custom logic."""
        # Use receipt-focused template with custom additions
        custom_prompt = build_prompt(
            template_name=PromptTemplate.RECEIPT_FOCUSED,
            content_type='financial',
            language='English'
        )
        
        result = self.ocr.process_image(
            image_data,
            instructions=custom_prompt + "\n\nAdditionally, calculate any totals and highlight discrepancies."
        )
        
        return result
    
    def process_technical_diagram(self, image_data):
        """Process technical diagrams and flowcharts."""
        result = self.ocr.process_image(
            image_data,
            prompt_template=PromptTemplate.CODE_FOCUSED,
            content_type='diagram',
            instructions="""
            This is a technical diagram. Please:
            1. Describe the overall structure and layout
            2. Extract all text labels and annotations
            3. Describe connections and relationships
            4. Convert to a structured text representation
            """
        )
        
        return result

# Use custom processor
processor = CustomDocumentProcessor()

with open('financial_statement.jpg', 'rb') as f:
    result = processor.process_financial_document(f.read())
    print(result.text)
```

### Integration with Other Libraries

```python
import pandas as pd
from pathlib import Path

def process_directory(directory_path, output_csv=None):
    """Process all documents in a directory and create a summary."""
    
    loader = UnifiedDocumentLoader(
        ocr_provider='openai',
        prompt_template=PromptTemplate.DEFAULT,
        max_workers=6
    )
    
    results = []
    directory = Path(directory_path)
    
    for file_path in directory.glob('*'):
        if file_path.is_file():
            try:
                result = loader.load(str(file_path))
                
                results.append({
                    'filename': file_path.name,
                    'format': result.metadata.format.value,
                    'size_bytes': result.metadata.size_bytes,
                    'word_count': len(result.content.split()),
                    'char_count': len(result.content),
                    'processing_successful': True,
                    'content_preview': result.content[:100] + '...'
                })
                
            except Exception as e:
                results.append({
                    'filename': file_path.name,
                    'error': str(e),
                    'processing_successful': False
                })
    
    # Create summary DataFrame
    df = pd.DataFrame(results)
    
    if output_csv:
        df.to_csv(output_csv, index=False)
    
    return df

# Process entire directory
summary = process_directory('./documents/', 'processing_summary.csv')
print(summary.head())
```

## 📊 Performance Optimization

### Optimal Settings for Different Scenarios

```python
# High-accuracy scenario (legal, medical documents)
high_accuracy_loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    model='gpt-4.1',
    temperature=0,              # Maximum determinism
    max_tokens=4096,           # Full context
    max_retries=5,             # More retries for reliability
    prompt_template=PromptTemplate.DOCUMENT_FOCUSED
)

# High-speed scenario (bulk processing)
high_speed_loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    model='gpt-4.1',
    temperature=0.1,           # Slight creativity for speed
    max_tokens=2048,           # Shorter responses
    max_workers=15,            # High concurrency
    enable_langchain=True,     # Efficient batch processing
    timeout=30,                # Shorter timeout
    prompt_template=PromptTemplate.DEFAULT
)

# Balanced scenario (general use)
balanced_loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    model='gpt-4.1',
    temperature=0.05,
    max_tokens=3072,
    max_workers=8,
    enable_langchain=True,
    max_retries=3,
    prompt_template=PromptTemplate.DEFAULT
)
```

## 📊 Parameter Exposure and Control

All parameters are now explicitly exposed in the function signatures for better transparency and control. This design choice helps users understand exactly what options are available without digging through documentation or source code.

### Why Explicit Parameters?

1. **Discoverability**: IDEs can show all available parameters with autocomplete
2. **Type Safety**: Each parameter has explicit type hints
3. **Documentation**: Each parameter is documented in the docstring
4. **No Hidden Behavior**: Users know exactly what they can control

### Complete Parameter Control Example

```python
# Initialize with full control
loader = UnifiedDocumentLoader(
    # OCR Provider
    ocr_provider='openai',
    api_key='your-api-key',
    
    # Model Configuration
    model='gpt-4.1',
    temperature=0.1,
    max_tokens=4096,
    
    # Batch Processing
    max_workers=8,
    
    # Prompt Configuration
    prompt_template=PromptTemplate.DEFAULT,
    
    # Reliability
    timeout=60,
    max_retries=5,
    
    # Advanced Parameters
    top_p=0.95,
    frequency_penalty=0.1,
    presence_penalty=0.1
)

# Process with full control
result = loader.load(
    'document.pdf',
    
    # Output Control
    output_format=OutputFormat.MARKDOWN,
    extract_images=True,
    ocr_images=True,
    preserve_layout=True,
    show_progress=True,
    
    # OCR Customization (per-document)
    language='English',
    content_type='document',
    instructions=None,  # Use default
    prompt_template_override=None,  # Use default
    
    # Image Handling
    save_images_locally=False,
    local_image_dir='./images',
    
    # Performance
    batch_size=None,  # Auto-determine
    
    # Format-specific
    encoding='utf-8',
    delimiter=None  # Auto-detect for CSV
)
```

## 🛠 Troubleshooting

### Common Issues and Solutions

```python
# 1. API Key Issues
try:
    loader = UnifiedDocumentLoader(ocr_provider='openai')
    # Test API key
    if hasattr(loader.ocr, 'validate_api_key'):
        if not loader.ocr.validate_api_key():
            print("❌ Invalid API key. Please check your OPENAI_API_KEY environment variable.")
except Exception as e:
    print(f"API key error: {e}")

# 2. Memory Issues with Large Documents
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    max_tokens=2048,           # Reduce token limit
    max_workers=3,             # Reduce concurrency
)

# 3. Timeout Issues
loader = UnifiedDocumentLoader(
    ocr_provider='openai',
    timeout=120,               # Increase timeout
    max_retries=5              # More retries
)

# 4. Language Detection Issues
result = loader.load(
    'unknown_language.pdf',
    prompt_template=PromptTemplate.MULTILINGUAL,
    language='auto-detect',    # Let the model detect
    content_type='document'
)
```

## 📚 API Reference

### UnifiedDocumentLoader

```python
class UnifiedDocumentLoader:
    def __init__(
        self,
        ocr_provider: Union[str, OCRProvider] = 'openai',
        api_key: Optional[str] = None,
        model: str = "gpt-4.1",
        temperature: float = 0,
        max_tokens: int = 4096,
        max_workers: int = 5,
        prompt_template: Union[str, PromptTemplate] = PromptTemplate.DEFAULT,
        enable_langchain: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs
    )
    
    def load(
        self,
        file_path: Union[str, Path],
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        **kwargs
    ) -> ProcessedDocument
```

### OpenAIOCR

```python
class OpenAIOCR:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1",
        temperature: float = 0,
        max_tokens: int = 4096,
        max_workers: int = 5,
        prompt_template: Optional[Union[str, PromptTemplate]] = None,
        enable_langchain: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs
    )
    
    def process_image(self, image_data: bytes, **kwargs) -> OCRResult
    def batch_process_images(self, images: List[bytes], **kwargs) -> List[OCRResult]
    def update_prompt_template(self, template_name: Union[str, PromptTemplate])
    def update_model_config(self, **kwargs)
    def get_configuration_summary(self) -> Dict[str, Any]
```

## 🔄 Migration Guide

### Upgrading from Earlier Versions

#### Method Name Changes
- `process_document()` → `load()`
- The new `load()` method has the same functionality with improved parameter handling

#### Parameter Changes
- `enable_langchain` parameter has been removed (LangChain is now always used for OpenAI OCR)
- Default `output_format` is now explicitly `OutputFormat.MARKDOWN`

#### OCR Result Format
- Image OCR results are now wrapped in `<image_ocr_result>...</image_ocr_result>` tags
- Previous format: `` `Image Description: {text}` ``
- New format: `<image_ocr_result>{text}</image_ocr_result>`

### Example Migration

```python
# Old code
result = loader.process_document('file.pdf')

# New code
result = loader.load('file.pdf')

# Old code with parameters
result = loader.process_document(
    'file.pdf',
    enable_langchain=True,  # No longer needed
    extract_images=True
)

# New code
result = loader.load(
    'file.pdf',
    extract_images=True,
    output_format=OutputFormat.MARKDOWN  # Explicit format
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/unifydoc/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/unifydoc/discussions)
- **Email**: luisleo52655@gmail.com

## ⚠️ Current Limitations

### Excel Sheet Selection
Currently, the library processes all sheets in Excel files. The `sheet_name` parameter shown in some examples is reserved for future functionality but not yet implemented. To process specific sheets, you may need to:
1. Extract the specific sheet to a separate file before processing
2. Post-process the JSON output to filter for specific sheet content

### Legacy Format Support
Legacy Office formats (DOC, XLS, PPT) require LibreOffice for conversion. Ensure LibreOffice is installed if you need to process these formats.

## 🌟 Acknowledgments

- OpenAI for GPT-4V capabilities
- LangChain for efficient batch processing
- The Python community for excellent document processing libraries