# GPT-ImgEval: Process Emu Dataset with ChatGPT

This repository contains a tool to automate processing the Facebook Emu Edit dataset with ChatGPT. It uploads images and prompts from the dataset to ChatGPT and saves the generated output images.

## Features

- Processes the Emu Edit dataset with ChatGPT
- Uses undetected-chromedriver to bypass Cloudflare detection
- Maintains a persistent Chrome profile for authentication
- Provides a coordinate-based approach for stable UI interaction
- Saves generated images directly to their source directories

## Requirements

- Python 3.7+
- Chrome browser installed
- The Emu Edit dataset downloaded

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd GPT-ImgEval
   ```

2. Install dependencies:
   ```bash
   pip install undetected-chromedriver selenium pyperclip pillow
   ```

3. Download the Emu Edit dataset (if you haven't already):
   ```bash
   # Option 1: Using the download_emu_dataset.py script (if included)
   python download_emu_dataset.py
   
   # Option 2: Download manually from Hugging Face
   # Visit https://huggingface.co/datasets/facebook/emu-edit
   # and download the dataset files
   ```

4. Ensure the dataset is structured as follows:
   ```
   emu-dataset/
   ├── 000001/
   │   ├── input.jpg
   │   └── prompt.txt
   ├── 000002/
   │   ├── input.jpg
   │   └── prompt.txt
   └── ...
   ```

## Usage

The main script is `undetected_gpt_processor.py`, which provides several modes and options for processing the dataset.

### Calibration Mode

Before running the processor, it's recommended to run the calibration mode to set up the correct UI element coordinates:

```bash
./undetected_gpt_processor.py --calibrate
```

This will:
1. Open a Chrome browser window
2. Guide you through logging in to ChatGPT
3. Help you identify the coordinates of key UI elements
4. Save these coordinates to a configuration file

### Running the Processor

After calibration, you can run the processor with:

```bash
./undetected_gpt_processor.py --config calibrated_config.json --use_coordinates --max_dirs 5
```

Command-line arguments:
- `--config <file>`: Path to configuration file (default: none)
- `--max_dirs <number>`: Maximum number of directories to process (default: process all)
- `--profile <path>`: Path to Chrome profile directory
- `--use_coordinates`: Use coordinate-based interaction instead of selectors
- `--calibrate`: Run calibration mode to identify UI element coordinates

### Example Configuration File

Here's an example of a configuration file (`emu_config.json`):

```json
{
  "headless": false,
  "chatgpt_url": "https://chat.openai.com",
  "image_gen_wait_time": 60,
  "max_dirs_to_process": 10,
  "dataset_dir": "emu-dataset",
  "browser_profile": "~/chrome_chatgpt_profile",
  "coordinates": {
    "attachment_button": {"x": 740, "y": 650},
    "textarea": {"x": 640, "y": 650},
    "first_image": {"x": 400, "y": 400},
    "generated_image": {"x": 400, "y": 500}
  },
  "use_coordinates": true
}
```