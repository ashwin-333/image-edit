# GPT Automation Pipeline

An automation tool for generating images with ChatGPT's 4o through browser automation.

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

## Input Directory Structure

The tool expects data organized in the following structure:

```
inputs/
├── images/
│   ├── 0000.png
│   ├── 0001.png
│   └── ...
└── edits/
    ├── 0000.txt
    ├── 0001.txt
    └── ...
```

- **images/**: Contains PNG image files with numeric names
- **edits/**: Contains text files with corresponding prompts

## Usage

### Recommended Usage (Parallel Processing)

For faster generation with multiple browser instances:

```bash
python undetected_gpt_processor.py --input_dir inputs --output_dir outputs --parallel --processes 2 --max_dirs 2
```

This will:
- Use the `inputs` directory for source images and prompts
- Save results to the `outputs` directory
- Launch 2 parallel Chrome instances, each processing prompts simultaneously
- Process a maximum of 2 directories per worker (adjust as needed)

### Command Line Options

```
--input_dir PATH     Directory containing 'images' and 'edits' subdirectories
--output_dir PATH    Directory to save generated images
--parallel           Enable parallel processing with multiple browser instances
--processes N        Number of parallel browser instances to use (default: 8)
--max_dirs N         Maximum number of directories to process (default: all)
--profile PATH       Path to Chrome user profile directory
--config PATH        Path to custom configuration file
--use_coordinates    Use coordinate-based interaction instead of selectors
--calibrate          Run calibration mode to identify UI element coordinates
```

### First Run Authentication

On the first batch, you'll need to manually log in to ChatGPT in each of the automated browser windows. Once authenticated, the browser will maintain your session for subsequent batches.

## Output Directory Structure

Generated images are saved in the specified output directory:

```
outputs/
├── 0000/
│   └── 0000.png  # Resized to match input image dimensions
├── 0001/
│   └── 0001.png
└── ...
```

The output images are automatically resized to match the dimensions of the corresponding input images, ensuring consistent aspect ratios and sizes.