# GPT Automation Pipeline

A powerful automation tool for generating images with ChatGPT's DALLE-3 integration through browser automation.

## Overview

This tool provides a robust framework for automating browser interactions with ChatGPT to generate images from text prompts. It features:

1. Undetected browser automation to avoid detection mechanisms
2. Parallel processing with multiple browser instances
3. Automatic handling of authentication and session management
4. Comprehensive logging and statistics tracking
5. Configurable processing options and timeout handling

## Requirements

- Python 3.8+
- Chrome browser
- Internet connection with access to chat.openai.com

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ashwin-333/image-edit.git
   cd image-edit
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install undetected-chromedriver selenium pillow
   ```

## Creating Input Data

The tool expects prompt data organized in directories:

```
emu-dataset/
├── 0000/
│   └── prompts.txt
│   ├── input.jpg
├── 0001/
│   └── prompts.txt
│   ├── input.jpg
└── ...
```

## Usage

### Basic Usage

Run the processor directly using:

```bash
python undetected_gpt_processor.py
```

### Parallel Processing (Recommended)

For faster generation with multiple browser instances:

```bash
python undetected_gpt_processor.py --parallel --processes 2 --max_dirs 2
```

This will launch 2 parallel Chrome instances, each processing prompts simultaneously, and will process a maximum of 2 images for each browser, so 4 total.

### Command Line Options

```
--parallel           Enable parallel processing with multiple browser instances
--processes N        Number of parallel browser instances to use (default: 2)
--max_dirs N         Maximum number of directories to process (default: all)
--headless           Run browser in headless mode (hidden)
--profile PATH       Path to Chrome user profile directory
--config PATH        Path to custom configuration file
--output_dir PATH    Directory to save generated images
--timeout SECONDS    Browser operation timeout in seconds
```

### First Batch Authentication

On the first batch, you'll need to manually log in to ChatGPT in each of the automated browser windows.

## Output Structure

Generated images and metadata are saved in the output directory:

```
emu-dataset/
├── 0000/
│   └── prompts.txt
│   ├── input.jpg
│   ├── output.jpg
│   ├── output.txt
├── 0001/
│   └── prompts.txt
│   ├── input.jpg
│   ├── output.jpg
│   ├── output.txt
└── ...
```