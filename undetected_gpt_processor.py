#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChatGPT Automation for Emu Dataset using undetected-chromedriver

This script uses undetected-chromedriver to better bypass Cloudflare protection
when automating interactions with ChatGPT for the Emu dataset.
"""

import os
import json
import time
import argparse
import traceback
from datetime import datetime
from pathlib import Path

# Try to import undetected-chromedriver
try:
    import undetected_chromedriver as uc
except ImportError:
    print("Error: undetected-chromedriver is not installed.")
    print("Please install it with: pip install undetected-chromedriver")
    exit(1)

# Standard selenium imports
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


class EmuGPTProcessor:
    """Process Emu dataset using undetected-chromedriver for better Cloudflare bypass"""
    
    def __init__(self, config_path=None):
        """Initialize with configuration"""
        self.config = self.load_config(config_path)
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "processing_times": [],
            "total_time": 0
        }
        self.driver = None
        self.user_profile = os.path.join(os.path.expanduser("~"), "chrome_chatgpt_profile")
    
    def load_config(self, config_path):
        """Load configuration from file"""
        default_config = {
            "headless": False,  # Always use visible browser for Cloudflare bypass
            "chatgpt_url": "https://chat.openai.com",
            "image_gen_wait_time": 60,
            "max_dirs_to_process": 0,  # 0 means process all
            "dataset_dir": "emu-dataset",
            "browser_profile": os.path.join(os.path.expanduser("~"), "chrome_chatgpt_profile"),
            # Add coordinates for UI elements
            "coordinates": {
                "attachment_button": {"x": 740, "y": 650},  # Default coordinates for attachment button
                "textarea": {"x": 640, "y": 650},           # Default coordinates for textarea
                "first_image": {"x": 400, "y": 400},        # Default coordinates for first image (to skip)
                "generated_image": {"x": 400, "y": 500}     # Default coordinates for generated image
            },
            "use_coordinates": False  # Whether to use coordinates instead of selectors
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                    
                    # Handle coordinates specially to merge them correctly
                    if "coordinates" in custom_config:
                        default_config["coordinates"].update(custom_config["coordinates"])
                        del custom_config["coordinates"]
                        
                    default_config.update(custom_config)
                    
                    # Update user profile from config if provided
                    if "browser_profile" in custom_config:
                        self.user_profile = custom_config["browser_profile"]
            except Exception as e:
                print(f"Error loading config: {str(e)}")
        
        # Always update user_profile from config
        self.user_profile = default_config["browser_profile"]
        return default_config
    
    def save_stats(self):
        """Save statistics to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = f"emu_stats_{timestamp}.json"
        
        # Add summary statistics
        if self.stats["successful"] > 0:
            avg_time = sum(self.stats["processing_times"]) / self.stats["successful"]
            hourly_rate = 3600 / avg_time if avg_time > 0 else 0
            
            self.stats["avg_time"] = avg_time
            self.stats["hourly_rate"] = hourly_rate
        
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            print(f"Statistics saved to {stats_file}")
        except Exception as e:
            print(f"Error saving statistics: {str(e)}")
    
    def setup_browser(self):
        """Set up undetected-chromedriver browser"""
        print("Setting up undetected Chrome browser...")
        
        # Create profile directory if it doesn't exist
        os.makedirs(self.user_profile, exist_ok=True)
        print(f"Using Chrome profile at: {self.user_profile}")
        
        # Configure options
        options = uc.ChromeOptions()
        
        # Always use visible browser for Cloudflare bypass
        headless = False  # Force visible mode
        
        # Additional options to help with Cloudflare
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,800")
        
        # Create the undetected Chrome driver with user profile
        driver = uc.Chrome(
            user_data_dir=self.user_profile,
            options=options,
            headless=headless,
            use_subprocess=True
        )
        
        # Set window size
        driver.set_window_size(1280, 800)
        
        return driver
    
    def authenticate(self):
        """Ensure authentication to ChatGPT"""
        print("Navigating to ChatGPT...")
        self.driver.get(self.config["chatgpt_url"])
        
        print("\n=================================================")
        print("MANUAL LOGIN INSTRUCTIONS")
        print("1. Complete any verification challenges if needed")
        print("2. Log in to your ChatGPT account if not already logged in")
        print("3. Wait for the chat interface to load completely")
        print("=================================================\n")
        
        # Use manual confirmation instead of waiting for elements
        manual_confirm = input("Have you completed login and can see the chat interface? (y/n): ").strip().lower()
        
        if manual_confirm in ['y', 'yes']:
            print("Continuing with processing...")
            return True
        else:
            print("Login not confirmed. Exiting.")
            return False
    
    def click_at_coordinates(self, x, y, description="element"):
        """Click at specific coordinates on the screen"""
        try:
            print(f"Clicking at coordinates ({x}, {y}) for {description}...")
            self.driver.execute_script(f"window.scrollTo(0, {max(0, y-300)});")  # Scroll to make element visible
            time.sleep(0.5)
            action = ActionChains(self.driver)
            action.move_by_offset(x, y).click().perform()
            action.reset_actions()  # Reset action chains
            print(f"Clicked at ({x}, {y})")
            return True
        except Exception as e:
            print(f"Error clicking at coordinates ({x}, {y}): {str(e)}")
            return False
    
    def input_text_at_coordinates(self, x, y, text, description="textarea"):
        """Click at coordinates and input text"""
        try:
            print(f"Entering text at coordinates ({x}, {y}) for {description}...")
            self.click_at_coordinates(x, y, description)
            time.sleep(0.5)
            action = ActionChains(self.driver)
            action.send_keys(text).perform()
            print(f"Entered text at ({x}, {y})")
            return True
        except Exception as e:
            print(f"Error entering text at coordinates ({x}, {y}): {str(e)}")
            return False
    
    def screenshot_area(self, x, y, width, height, output_file, description="area"):
        """Take a screenshot of a specific area"""
        try:
            print(f"Taking screenshot of {description} at ({x}, {y})...")
            self.driver.execute_script(f"window.scrollTo(0, {max(0, y-300)});")  # Scroll to make element visible
            time.sleep(0.5)
            
            # Take full screenshot
            full_screenshot = self.driver.get_screenshot_as_png()
            from PIL import Image
            import io
            
            # Open the screenshot
            image = Image.open(io.BytesIO(full_screenshot))
            
            # Crop to the desired area
            cropped = image.crop((x, y, x + width, y + height))
            
            # Save the cropped image
            cropped.save(output_file)
            print(f"Screenshot saved to {output_file}")
            return True
        except Exception as e:
            print(f"Error taking screenshot at ({x}, {y}): {str(e)}")
            return False
    
    def process_directory(self, directory_path):
        """Process a single directory with input image and prompt"""
        dir_name = os.path.basename(directory_path)
        print(f"\nProcessing directory: {dir_name}")
        
        # Check for required files
        input_image = os.path.join(directory_path, "input.jpg")
        prompt_file = os.path.join(directory_path, "prompt.txt")
        
        if not os.path.exists(input_image) or not os.path.exists(prompt_file):
            print(f"Skipping {dir_name} - missing files")
            return False
        
        # Read prompt
        with open(prompt_file, 'r') as f:
            prompt = f.read().strip()
        
        print(f"Prompt: {prompt}")
        print(f"Input image: {input_image}")
        
        start_time = time.time()
        success = False
        
        try:
            # Start a new chat
            print("Starting a new chat...")
            self.driver.get(self.config["chatgpt_url"])
            time.sleep(3)
            
            # Let the user confirm they can see the chat interface
            ready_to_proceed = input("Is the chat interface loaded and ready? (y/n): ").strip().lower()
            if ready_to_proceed not in ['y', 'yes']:
                print("User indicated chat interface is not ready, aborting this directory.")
                return False
            
            # Check if we should use coordinates
            use_coordinates = self.config.get("use_coordinates", False)
            coordinates = self.config.get("coordinates", {})
            
            if use_coordinates:
                print("Using coordinate-based interaction mode")
                
                # Click attachment button
                attachment_coords = coordinates.get("attachment_button", {"x": 740, "y": 650})
                if not self.click_at_coordinates(attachment_coords["x"], attachment_coords["y"], "attachment button"):
                    manual_click = input("Failed to click attachment button. Please click it manually, then type 'done': ").strip().lower()
                    if manual_click != 'done':
                        print("Aborting this directory.")
                        return False
                
                time.sleep(1)
                
                # Now we need to handle file upload
                # Since we can't directly access the file input with coordinates,
                # we'll try to find it by selector first
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                
                if file_inputs:
                    file_inputs[0].send_keys(os.path.abspath(input_image))
                    print("Image uploaded")
                else:
                    print("File input not found")
                    manual_upload = input("Please upload the image manually, then type 'done': ").strip().lower()
                    if manual_upload != 'done':
                        print("Aborting this directory.")
                        return False
                
                time.sleep(2)
                
                # Enter text in textarea
                textarea_coords = coordinates.get("textarea", {"x": 640, "y": 650})
                if not self.input_text_at_coordinates(textarea_coords["x"], textarea_coords["y"], prompt, "textarea"):
                    manual_prompt = input("Failed to enter prompt. Please enter it manually, then type 'done': ").strip().lower()
                    if manual_prompt != 'done':
                        print("Aborting this directory.")
                        return False
                
                # Send the message with Enter key
                action = ActionChains(self.driver)
                action.send_keys(Keys.RETURN).perform()
                print("Message sent, waiting for response...")
                
            else:
                # Use selector-based approach (original code)
                try:
                    # Look for attachment button and click it
                    print("Looking for attachment button...")
                    attachment_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Attach files"]')
                    
                    if not attachment_buttons:
                        attachment_buttons = self.driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Attach")]')
                    
                    if attachment_buttons:
                        attachment_buttons[0].click()
                        print("Clicked attachment button")
                    else:
                        print("Attachment button not found automatically")
                        manual_click = input("Please click the attachment button manually, then type 'done': ").strip().lower()
                        if manual_click != 'done':
                            print("Aborting this directory.")
                            return False
                    
                    time.sleep(1)
                    
                    # Now find the file input and send the file path
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                    
                    if file_inputs:
                        file_inputs[0].send_keys(os.path.abspath(input_image))
                        print("Image uploaded")
                    else:
                        print("File input not found")
                        manual_upload = input("Please upload the image manually, then type 'done': ").strip().lower()
                        if manual_upload != 'done':
                            print("Aborting this directory.")
                            return False
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error during file upload: {str(e)}")
                    manual_upload = input("Error occurred. Did you upload the image manually? (y/n): ").strip().lower()
                    if manual_upload not in ['y', 'yes']:
                        print("Aborting this directory.")
                        return False
                
                # Enter prompt
                try:
                    textareas = self.driver.find_elements(By.CSS_SELECTOR, 'textarea[placeholder="Message ChatGPT…"]')
                    
                    if textareas:
                        textarea = textareas[0]
                        textarea.clear()
                        textarea.send_keys(prompt)
                        print("Prompt entered")
                        textarea.send_keys(Keys.RETURN)
                        print("Message sent, waiting for response...")
                    else:
                        print("Textarea not found automatically")
                        manual_prompt = input("Please enter the prompt manually and press Enter, then type 'done': ").strip().lower()
                        if manual_prompt != 'done':
                            print("Aborting this directory.")
                            return False
                    
                except Exception as e:
                    print(f"Error entering prompt: {str(e)}")
                    manual_prompt = input("Error occurred. Did you enter the prompt manually? (y/n): ").strip().lower()
                    if manual_prompt not in ['y', 'yes']:
                        print("Aborting this directory.")
                        return False
            
            # Wait for response
            print("Waiting for response...")
            manual_response = input(f"Wait {self.config['image_gen_wait_time']} seconds, then press Enter when ChatGPT has fully generated a response with image: ")
            
            # Capture the result
            if use_coordinates:
                # Use coordinate-based approach for capturing the result
                output_file = os.path.join(directory_path, "output.png")
                
                # Try to capture the generated image using coordinates
                img_coords = coordinates.get("generated_image", {"x": 400, "y": 500})
                if self.screenshot_area(img_coords["x"], img_coords["y"], 512, 512, output_file, "generated image"):
                    print(f"Image saved to {output_file}")
                    success = True
                else:
                    print("Failed to capture image with coordinates")
                    full_screenshot_path = os.path.join(directory_path, "output_full.png")
                    self.driver.save_screenshot(full_screenshot_path)
                    print(f"Saved full screenshot to {full_screenshot_path}")
                    success = True
                
                # Try to get the response text (still using selectors as this is text)
                try:
                    response_elements = self.driver.find_elements(By.CSS_SELECTOR, '.markdown')
                    if response_elements:
                        response_text = response_elements[-1].text
                        output_txt = os.path.join(directory_path, "output.txt")
                        with open(output_txt, 'w') as f:
                            f.write(response_text)
                        print(f"Response saved to {output_txt}")
                    else:
                        print("Could not find response text automatically")
                        manual_text = input("Please copy the response text and paste it here (press Enter to skip): ")
                        if manual_text.strip():
                            output_txt = os.path.join(directory_path, "output.txt")
                            with open(output_txt, 'w') as f:
                                f.write(manual_text)
                            print(f"Response text saved manually to {output_txt}")
                except Exception as e:
                    print(f"Error capturing response text: {str(e)}")
                    manual_text = input("Error occurred. Please copy the response text and paste it here (press Enter to skip): ")
                    if manual_text.strip():
                        output_txt = os.path.join(directory_path, "output.txt")
                        with open(output_txt, 'w') as f:
                            f.write(manual_text)
                        print(f"Response text saved manually to {output_txt}")
                        
            else:
                # Use selector-based approach (original code)
                try:
                    # Look for the generated image
                    print("Looking for generated images...")
                    images = self.driver.find_elements(By.CSS_SELECTOR, 'img')
                    
                    if len(images) < 2:
                        print("Not enough images found")
                        manual_image_found = input("Do you see a generated image? (y/n): ").strip().lower()
                        if manual_image_found not in ['y', 'yes']:
                            print("No images found, skipping image capture")
                        else:
                            print("Taking a screenshot of the whole page instead...")
                            output_file = os.path.join(directory_path, "output_full.png")
                            self.driver.save_screenshot(output_file)
                            print(f"Full screenshot saved to {output_file}")
                            success = True
                    else:
                        # Skip the first image (usually the user uploaded one)
                        for i, img in enumerate(images):
                            if i == 0:  # Skip the first image (user uploaded)
                                continue
                                
                            try:
                                # Scroll to the image
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                                time.sleep(1)
                                
                                # Take screenshot of the image
                                output_file = os.path.join(directory_path, "output.png")
                                img.screenshot(output_file)
                                print(f"Image saved to {output_file}")
                                
                                # We found a valid image
                                success = True
                                break
                            except Exception as e:
                                print(f"Error capturing image {i}: {str(e)}")
                                continue
                    
                    # Try to get the response text
                    try:
                        response_elements = self.driver.find_elements(By.CSS_SELECTOR, '.markdown')
                        if response_elements:
                            response_text = response_elements[-1].text
                            output_txt = os.path.join(directory_path, "output.txt")
                            with open(output_txt, 'w') as f:
                                f.write(response_text)
                            print(f"Response saved to {output_txt}")
                            
                            # If we saved the text but not the image, still count as partial success
                            if not success:
                                print("Warning: Saved text but could not save image")
                                success = True
                        else:
                            print("Could not find response text automatically")
                            manual_text = input("Please copy the response text and paste it here (press Enter to skip): ")
                            if manual_text.strip():
                                output_txt = os.path.join(directory_path, "output.txt")
                                with open(output_txt, 'w') as f:
                                    f.write(manual_text)
                                print(f"Response text saved manually to {output_txt}")
                                success = True
                                
                    except Exception as e:
                        print(f"Error capturing response text: {str(e)}")
                        manual_text = input("Error occurred. Please copy the response text and paste it here (press Enter to skip): ")
                        if manual_text.strip():
                            output_txt = os.path.join(directory_path, "output.txt")
                            with open(output_txt, 'w') as f:
                                f.write(manual_text)
                            print(f"Response text saved manually to {output_txt}")
                            success = True
                    
                except Exception as e:
                    print(f"Error capturing response: {str(e)}")
                    traceback.print_exc()
                    
                    # Ask for manual intervention
                    manual_save = input("Would you like to manually save the output? (y/n): ").strip().lower()
                    if manual_save in ['y', 'yes']:
                        manual_text = input("Please copy the response text and paste it here (press Enter to skip): ")
                        if manual_text.strip():
                            output_txt = os.path.join(directory_path, "output.txt")
                            with open(output_txt, 'w') as f:
                                f.write(manual_text)
                            print(f"Response text saved manually to {output_txt}")
                            success = True
            
        except Exception as e:
            print(f"Error processing {dir_name}: {str(e)}")
            traceback.print_exc()
        
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Update stats
        self.stats["processed"] += 1
        if success:
            self.stats["successful"] += 1
            self.stats["processing_times"].append(processing_time)
        else:
            self.stats["failed"] += 1
        
        # Add processing time to output.txt if it exists
        if success and os.path.exists(os.path.join(directory_path, "output.txt")):
            output_txt = os.path.join(directory_path, "output.txt")
            try:
                with open(output_txt, 'a') as f:
                    f.write(f"\n\nProcessing time: {processing_time:.2f} seconds")
            except Exception as e:
                print(f"Error updating output.txt: {str(e)}")
        
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Status: {'Success' if success else 'Failed'}")
        
        return success
    
    def run(self):
        """Run the processing on the dataset"""
        print("ChatGPT Automation for Emu Dataset using undetected-chromedriver")
        print("=============================================================")
        
        # Start timing
        overall_start = time.time()
        
        # Check dataset directory
        dataset_dir = self.config["dataset_dir"]
        if not os.path.exists(dataset_dir):
            print(f"Error: Dataset directory '{dataset_dir}' not found")
            return False
        
        # Get directories to process
        all_dirs = sorted([d for d in os.listdir(dataset_dir) 
                     if os.path.isdir(os.path.join(dataset_dir, d))])
        
        if not all_dirs:
            print(f"No directories found in '{dataset_dir}'")
            return False
        
        # Filter out directories that already have output files
        dirs = []
        skipped_dirs = []
        
        for directory in all_dirs:
            dir_path = os.path.join(dataset_dir, directory)
            output_png = os.path.join(dir_path, "output.png")
            output_txt = os.path.join(dir_path, "output.txt")
            
            # Skip if both output files exist and are not empty
            if (os.path.exists(output_png) and os.path.getsize(output_png) > 0 and
                os.path.exists(output_txt) and os.path.getsize(output_txt) > 0):
                skipped_dirs.append(directory)
            else:
                dirs.append(directory)
        
        print(f"Found {len(all_dirs)} total directories")
        print(f"Skipping {len(skipped_dirs)} directories with existing outputs")
        print(f"Need to process {len(dirs)} directories")
        
        if not dirs:
            print("All directories have been processed already!")
            return True
        
        # Limit number of directories if specified
        max_dirs = self.config["max_dirs_to_process"]
        if max_dirs > 0 and len(dirs) > max_dirs:
            print(f"Limiting to {max_dirs} directories (from {len(dirs)} remaining)")
            dirs = dirs[:max_dirs]
        
        # Display directories to process
        print("\nFirst directories to process:")
        for i, directory in enumerate(dirs[:5], 1):
            print(f"({i}) {directory}" + ("..." if i == 5 and len(dirs) > 5 else ""))
        
        try:
            # Set up browser
            self.driver = self.setup_browser()
            
            # Authenticate
            auth_success = self.authenticate()
            if not auth_success:
                print("Authentication failed, cannot proceed.")
                self.driver.quit()
                return False
            
            # Process each directory
            for i, directory in enumerate(dirs, 1):
                dir_path = os.path.join(dataset_dir, directory)
                print(f"\n[{i}/{len(dirs)}] Processing: {directory}")
                
                # Check if we're still authenticated
                if i > 1 and i % 5 == 0:
                    print("Checking authentication status...")
                    if "login" in self.driver.current_url:
                        print("Session expired, attempting to re-authenticate...")
                        auth_success = self.authenticate()
                        if not auth_success:
                            print("Re-authentication failed, stopping processing.")
                            break
                
                # Process the directory
                success = self.process_directory(dir_path)
                
                # Add a short pause between directories
                if i < len(dirs):
                    time.sleep(2)
            
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            # Close browser
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")
        
        # Calculate overall time
        overall_end = time.time()
        self.stats["total_time"] = overall_end - overall_start
        
        # Display summary
        print("\n=== Processing Summary ===")
        print(f"Total directories processed: {self.stats['processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        
        # Calculate and display statistics
        if self.stats["successful"] > 0:
            avg_time = sum(self.stats["processing_times"]) / self.stats["successful"]
            hourly_rate = 3600 / avg_time
            
            print(f"\nAverage processing time: {avg_time:.2f} seconds per image")
            print(f"Data collection rate: {hourly_rate:.2f} images per hour")
            print(f"Total time: {self.stats['total_time']:.2f} seconds")
            
            # Format as hours, minutes, seconds
            hours, remainder = divmod(self.stats["total_time"], 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Total time: {int(hours)}h {int(minutes)}m {seconds:.2f}s")
        
        # Save statistics
        self.save_stats()
        
        return self.stats["successful"] > 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ChatGPT Automation for Emu Dataset using undetected-chromedriver")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--max_dirs", type=int, default=0, help="Maximum number of directories to process")
    parser.add_argument("--profile", type=str, help="Path to Chrome profile directory")
    parser.add_argument("--use_coordinates", action="store_true", help="Use coordinate-based interaction instead of selectors")
    parser.add_argument("--calibrate", action="store_true", help="Run calibration mode to identify UI element coordinates")
    
    args = parser.parse_args()
    
    # Create processor
    processor = EmuGPTProcessor(args.config)
    
    # Check if we should run calibration mode
    if args.calibrate:
        return run_calibration_mode(processor)
    
    # Override config with command line arguments
    if args.max_dirs > 0:
        processor.config["max_dirs_to_process"] = args.max_dirs
    if args.profile:
        processor.config["browser_profile"] = args.profile
        processor.user_profile = args.profile
    if args.use_coordinates:
        processor.config["use_coordinates"] = True
    
    # Run processing
    success = processor.run()
    
    return 0 if success else 1

def run_calibration_mode(processor):
    """Run in calibration mode to identify UI element coordinates"""
    print("Running in CALIBRATION MODE")
    print("This will help you determine the coordinates of ChatGPT UI elements")
    print("Follow the instructions carefully...")
    
    # Set up browser
    processor.driver = processor.setup_browser()
    
    try:
        # Go to ChatGPT
        processor.driver.get(processor.config["chatgpt_url"])
        print("Navigating to ChatGPT...")
        
        # Wait for login
        print("\n=================================================")
        print("MANUAL LOGIN INSTRUCTIONS")
        print("1. Complete any verification challenges if needed")
        print("2. Log in to your ChatGPT account if not already logged in")
        print("3. Wait for the chat interface to load completely")
        print("=================================================\n")
        
        input("Press Enter when you are logged in and can see the chat interface...")
        
        # Help user identify coordinates
        print("\nMOUSE COORDINATE CALIBRATION")
        print("1. To identify coordinates, move your mouse to the UI element")
        print("2. Press Ctrl+Shift+I to open developer tools")
        print("3. Click on the Console tab")
        print("4. Paste this code and press Enter:")
        print("   document.addEventListener('mousemove', e => console.log(`Mouse X: ${e.clientX}, Y: ${e.clientY}`));")
        print("5. Move your mouse over the UI elements and note the coordinates")
        print("6. When done, close the developer tools")
        
        # Collect coordinates
        coordinates = {}
        
        print("\nPlease move your mouse to the ATTACHMENT BUTTON and note its coordinates")
        x = int(input("Enter X coordinate for attachment button: "))
        y = int(input("Enter Y coordinate for attachment button: "))
        coordinates["attachment_button"] = {"x": x, "y": y}
        
        print("\nPlease move your mouse to the TEXTAREA and note its coordinates")
        x = int(input("Enter X coordinate for textarea: "))
        y = int(input("Enter Y coordinate for textarea: "))
        coordinates["textarea"] = {"x": x, "y": y}
        
        print("\nAfter sending a message with an image, move your mouse to where the GENERATED IMAGE appears")
        print("If unsure, you can skip this step by entering 0 for both coordinates")
        x = int(input("Enter X coordinate for generated image: "))
        y = int(input("Enter Y coordinate for generated image: "))
        if x > 0 and y > 0:
            coordinates["generated_image"] = {"x": x, "y": y}
        
        # Save coordinates to config file
        config_file = processor.config_manager.config_file if hasattr(processor, 'config_manager') else "calibrated_config.json"
        if not config_file or config_file == "calibrated_config.json":
            config_file = input("Enter filename to save calibration (default: calibrated_config.json): ").strip()
            if not config_file:
                config_file = "calibrated_config.json"
        
        # Create or update config file
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = processor.config.copy()
            
            # Update coordinates
            config["coordinates"] = coordinates
            config["use_coordinates"] = True
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"\nCalibration saved to {config_file}")
            print(f"To use these coordinates, run with: --config {config_file} --use_coordinates")
            
        except Exception as e:
            print(f"Error saving calibration: {str(e)}")
        
        return 0
        
    except Exception as e:
        print(f"Error during calibration: {str(e)}")
        traceback.print_exc()
        return 1
    finally:
        if processor.driver:
            processor.driver.quit()
            print("Browser closed")


if __name__ == "__main__":
    import sys
    sys.exit(main()) 