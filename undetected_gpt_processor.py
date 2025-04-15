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
        # Use the specific Chrome profile path
        self.user_profile = "/Users/tejas/chrome_chatgpt_profile_20250414_214423"
    
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
                    print("Looking for the + button for attachment...")
                    
                    # Wait for the page to fully load
                    time.sleep(5)
                    
                    # Try to find the + button directly
                    plus_button = None
                    
                    # Attempt 1: Try finding button with the exact + character
                    plus_buttons = self.driver.find_elements(By.XPATH, '//button[normalize-space(.)="+"]')
                    if plus_buttons:
                        plus_button = plus_buttons[0]
                        print("Found + button by exact text")
                    
                    # Attempt 2: Try finding by looking at the first button in the toolbar
                    if not plus_button:
                        toolbar_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.flex.items-center button')
                        if toolbar_buttons and len(toolbar_buttons) > 0:
                            plus_button = toolbar_buttons[0]  # First button is usually +
                            print("Found first button in toolbar")
                    
                    # Attempt 3: Try by data-testid if available
                    if not plus_button:
                        data_test_buttons = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="chat-composer-add-button"]')
                        if data_test_buttons:
                            plus_button = data_test_buttons[0]
                            print("Found + button by data-testid")
                    
                    # Click the + button if found
                    if plus_button:
                        try:
                            # Scroll to make it visible
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", plus_button)
                            time.sleep(1)
                            
                            # Try clicking with JavaScript
                            self.driver.execute_script("arguments[0].click();", plus_button)
                            print("Clicked + button")
                        except Exception as click_error:
                            print(f"Error clicking with JavaScript: {click_error}")
                            try:
                                # Try the regular click
                                plus_button.click()
                                print("Clicked + button regularly")
                            except Exception as direct_click_error:
                                print(f"Error with direct click too: {direct_click_error}")
                                print("Falling back to coordinates approach")
                                raise Exception("Could not click the + button")
                    else:
                        print("+ button not found by any selector")
                        
                        # Take a screenshot to help debug
                        debug_screenshot = os.path.join(directory_path, "debug_screenshot.png")
                        self.driver.save_screenshot(debug_screenshot)
                        print(f"Saved debug screenshot to {debug_screenshot}")
                        
                        # Try to click at the UPDATED coordinates of the + button from the new screenshot
                        try:
                            # Updated coordinates based on the new screenshot
                            x, y = 420, 380  # Approximate coordinates for the + button in the toolbar
                            self.click_at_coordinates(x, y, "+ button")
                            print("Clicked at coordinates of + button")
                            time.sleep(2)  # Wait longer after coordinate click
                        except Exception as coord_error:
                            print(f"Error clicking at coordinates: {coord_error}")
                            
                            # Try several positions if first one fails
                            for x_offset in [-10, 0, 10, 20]:
                                for y_offset in [-10, 0, 10]:
                                    try:
                                        new_x, new_y = 420 + x_offset, 380 + y_offset
                                        print(f"Trying alternate coordinates: ({new_x}, {new_y})")
                                        self.click_at_coordinates(new_x, new_y, "alternate + button position")
                                        time.sleep(1)
                                    except:
                                        continue
                        
                        manual_click = input("Please click the + button manually, then type 'done': ").strip().lower()
                        if manual_click != 'done':
                            print("Aborting this directory.")
                            return False
                    
                    # Give the dropdown menu time to appear
                    time.sleep(2)
                    
                    # Look for the "Upload file" option in the dropdown menu
                    upload_option_found = False
                    
                    # Try multiple selectors for the upload option
                    upload_selectors = [
                        '//*[contains(text(), "Upload") and contains(text(), "file")]',
                        '//*[contains(text(), "Upload")]',
                        '//*[contains(@aria-label, "upload")]',
                        '//*[contains(@role, "menuitem") and contains(., "Upload")]'
                    ]
                    
                    for selector in upload_selectors:
                        try:
                            upload_options = self.driver.find_elements(By.XPATH, selector)
                            if upload_options and len(upload_options) > 0:
                                # Scroll to the upload option
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", upload_options[0])
                                time.sleep(0.5)
                                
                                # Click the upload option
                                self.driver.execute_script("arguments[0].click();", upload_options[0])
                                print(f"Clicked upload option using selector: {selector}")
                                upload_option_found = True
                                time.sleep(1)
                                break
                        except:
                            continue
                    
                    # If no upload option found, try clicking near where it should be
                    if not upload_option_found:
                        try:
                            # Try clicking where the "Upload file" option typically appears
                            # These coordinates are relative to the + button
                            upload_x, upload_y = 450, 410
                            self.click_at_coordinates(upload_x, upload_y, "Upload file option")
                            print("Tried clicking at upload option coordinates")
                            time.sleep(1)
                        except Exception as upload_coord_error:
                            print(f"Error clicking at upload coordinates: {upload_coord_error}")
                    
                    # Now find the file input and send the file path
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                    
                    if file_inputs:
                        file_inputs[0].send_keys(os.path.abspath(input_image))
                        print("Image uploaded")
                    else:
                        # Try again after a delay - sometimes file input appears later
                        time.sleep(2)
                        file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                        if file_inputs:
                            file_inputs[0].send_keys(os.path.abspath(input_image))
                            print("Image uploaded on second attempt")
                        else:
                            print("File input not found")
                            manual_upload = input("Please upload the image manually, then type 'done': ").strip().lower()
                            if manual_upload != 'done':
                                print("Aborting this directory.")
                                return False
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error during file upload: {str(e)}")
                    traceback.print_exc()
                    manual_upload = input("Error occurred. Did you upload the image manually? (y/n): ").strip().lower()
                    if manual_upload not in ['y', 'yes']:
                        print("Aborting this directory.")
                        return False
                
                # Enter prompt
                try:
                    print("Looking for textarea to enter prompt...")
                    
                    # Wait for the textarea to be ready after image upload
                    time.sleep(3)
                    
                    # Try multiple approaches to find the textarea
                    textarea = None
                    
                    # Approach 1: Standard placeholder selector
                    textareas = self.driver.find_elements(By.CSS_SELECTOR, 'textarea[placeholder="Message ChatGPT…"]')
                    if textareas:
                        textarea = textareas[0]
                        print("Found textarea by placeholder")
                    
                    # Approach 2: Try with a more general textarea selector
                    if not textarea:
                        textareas = self.driver.find_elements(By.CSS_SELECTOR, 'textarea[placeholder*="Message"]')
                        if textareas:
                            textarea = textareas[0]
                            print("Found textarea by partial placeholder")
                    
                    # Approach 3: Try with data-testid
                    if not textarea:
                        textareas = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="chat-composer-textarea"] textarea')
                        if textareas:
                            textarea = textareas[0]
                            print("Found textarea by data-testid")
                    
                    # Approach 4: Try any textarea
                    if not textarea:
                        textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')
                        if textareas:
                            # Try to find visible textareas
                            for text_area in textareas:
                                if text_area.is_displayed():
                                    textarea = text_area
                                    print("Found visible textarea")
                                    break
                    
                    # Try to enter text if textarea found
                    if textarea:
                        try:
                            # Scroll to make the textarea visible
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
                            time.sleep(1)
                            
                            # First try to focus and clear any existing text
                            self.driver.execute_script("arguments[0].focus();", textarea)
                            self.driver.execute_script("arguments[0].value = '';", textarea)
                            time.sleep(0.5)
                            
                            # Method 1: Standard send_keys
                            textarea.send_keys(prompt)
                            print("Entered prompt via send_keys")
                            
                            # Wait a moment before pressing Enter
                            time.sleep(1)
                            textarea.send_keys(Keys.RETURN)
                            print("Message sent, waiting for response...")
                        except Exception as text_error:
                            print(f"Error with standard input: {text_error}")
                            try:
                                # Method 2: Use JavaScript to set value and dispatch events
                                self.driver.execute_script("""
                                    arguments[0].value = arguments[1];
                                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                                """, textarea, prompt)
                                time.sleep(1)
                                
                                # Try to send Enter via JavaScript
                                self.driver.execute_script("""
                                    var keyEvent = new KeyboardEvent('keydown', {
                                        'key': 'Enter',
                                        'code': 'Enter',
                                        'keyCode': 13,
                                        'bubbles': true
                                    });
                                    arguments[0].dispatchEvent(keyEvent);
                                """, textarea)
                                print("Entered prompt and sent via JavaScript")
                            except Exception as js_error:
                                print(f"Error with JavaScript input: {js_error}")
                                # Method 3: Try Action Chains
                                try:
                                    actions = ActionChains(self.driver)
                                    actions.move_to_element(textarea).click().send_keys(prompt).send_keys(Keys.RETURN).perform()
                                    print("Entered prompt via Action Chains")
                                except Exception as action_error:
                                    print(f"Error with Action Chains: {action_error}")
                                    raise Exception("Could not enter text using any method")
                    else:
                        print("Textarea not found by any selector")
                        
                        # Take a screenshot to help debug
                        debug_screenshot = os.path.join(directory_path, "debug_textarea.png")
                        self.driver.save_screenshot(debug_screenshot)
                        print(f"Saved debug screenshot to {debug_screenshot}")
                        
                        # Try clicking where textarea should be and entering text
                        try:
                            # Approximate coordinates for textarea in the chat interface
                            textarea_x, textarea_y = 640, 650
                            self.click_at_coordinates(textarea_x, textarea_y, "textarea area")
                            time.sleep(1)
                            
                            # Send text using Action Chains since we don't have an element
                            actions = ActionChains(self.driver)
                            actions.send_keys(prompt).send_keys(Keys.RETURN).perform()
                            print("Tried entering text at coordinates")
                        except Exception as coord_text_error:
                            print(f"Error entering text at coordinates: {coord_text_error}")
                            
                            # Ask for manual intervention
                            manual_prompt = input("Please enter the prompt manually and press Enter, then type 'done': ").strip().lower()
                            if manual_prompt != 'done':
                                print("Aborting this directory.")
                                return False
                    
                except Exception as e:
                    print(f"Error entering prompt: {str(e)}")
                    traceback.print_exc()
                    manual_prompt = input("Error occurred. Did you enter the prompt manually? (y/n): ").strip().lower()
                    if manual_prompt not in ['y', 'yes']:
                        print("Aborting this directory.")
                        return False
            
            # Wait for response
            print("Waiting for response...")
            
            # Wait longer for image generation
            wait_time = self.config['image_gen_wait_time']
            print(f"Waiting {wait_time} seconds for image generation to complete...")
            
            # Since image generation can take time, implement a better waiting approach
            start_wait = time.time()
            image_found = False
            
            # Keep checking for the generated image while waiting
            while time.time() - start_wait < wait_time and not image_found:
                try:
                    # Check if any images have appeared in the response
                    images = self.driver.find_elements(By.CSS_SELECTOR, 'img:not([alt="User"])') 
                    
                    # Find images in the response area (not the user's uploaded image)
                    response_images = []
                    
                    # Get all messages/blocks in the conversation
                    message_blocks = self.driver.find_elements(By.CSS_SELECTOR, '.w-full.text-token-text-primary')
                    
                    if message_blocks and len(message_blocks) >= 2:
                        # Last message block should be the assistant's response
                        last_block = message_blocks[-1]
                        
                        # Try to find images within this response block
                        response_images = last_block.find_elements(By.TAG_NAME, 'img')
                        
                        if response_images:
                            print(f"Found {len(response_images)} images in the latest response")
                            image_found = True
                            break
                    
                    # If no images found in message blocks, try broader search
                    if not image_found and images and len(images) >= 2:
                        # First image is usually the user's uploaded one, so look at the rest
                        for i, img in enumerate(images):
                            if i == 0:
                                continue  # Skip the first image (likely user's upload)
                                
                            # Check if it's a generated image
                            src = img.get_attribute('src')
                            if src and ('blob:' in src or 'data:' in src or 'openai' in src):
                                response_images.append(img)
                                image_found = True
                                break
                    
                    # If still no images found, but we see a loading indicator, keep waiting
                    if not image_found:
                        loading_indicators = self.driver.find_elements(By.CSS_SELECTOR, '.animate-spin')
                        if loading_indicators and any(indicator.is_displayed() for indicator in loading_indicators):
                            print("Generation in progress, still waiting...")
                            time.sleep(2)
                            continue
                        
                except Exception as e:
                    print(f"Error while checking for images: {e}")
                
                # Wait a bit before checking again
                time.sleep(2)
                
                # Print progress updates every 10 seconds
                elapsed = time.time() - start_wait
                if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                    print(f"Still waiting... {int(elapsed)}/{wait_time} seconds elapsed")
            
            manual_response = input("Has ChatGPT fully generated a response with image? (y/n): ").strip().lower()
            if manual_response not in ['y', 'yes']:
                # Give more time if the user says generation isn't complete
                print("Waiting for additional time...")
                time.sleep(10)
            
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
                    # Try to find and save the image using selectors
                    success = self.find_and_save_generated_image(directory_path)
            else:
                # Try to find and save the generated image using selectors
                success = self.find_and_save_generated_image(directory_path)
                
                if not success:
                    print("Could not save the image automatically, taking full screenshot")
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

    def test_browser(self):
        """Test browser functionality and responsiveness"""
        print("\nRunning browser test...")
        
        try:
            # 1. Test navigation to Google (a simple site)
            print("Testing navigation to Google...")
            self.driver.get("https://www.google.com")
            time.sleep(3)
            
            # 2. Test basic interaction
            print("Testing basic interaction...")
            search_box = self.driver.find_elements(By.NAME, "q")
            if search_box:
                print("  ✓ Found search box")
                search_box[0].send_keys("Test")
                time.sleep(1)
                search_box[0].clear()
                print("  ✓ Interaction successful")
            else:
                print("  ✗ Could not find search box")
                
            # 3. Test JavaScript execution
            print("Testing JavaScript execution...")
            user_agent = self.driver.execute_script("return navigator.userAgent")
            print(f"  ✓ User Agent: {user_agent}")
            
            # 4. Test browser state
            print("Browser information:")
            print(f"  - Window size: {self.driver.get_window_size()}")
            
            print("\nBrowser test completed.")
            print("If all tests passed but ChatGPT site is still unresponsive:")
            print("1. Try with a completely new Chrome profile")
            print("2. Make sure Chrome is up to date")
            print("3. OpenAI might be blocking automated access")
            print("4. Try the --use_coordinates option for alternative interaction method\n")
            
            return True
        except Exception as e:
            print(f"Error during browser test: {str(e)}")
            traceback.print_exc()
            return False

    def find_and_save_generated_image(self, directory_path):
        """Find and save the generated image from ChatGPT's response"""
        print("Searching for generated image...")
        
        try:
            # Different strategies to find the generated image
            # 1. Look for images in the assistant's response block
            message_blocks = self.driver.find_elements(By.CSS_SELECTOR, '.w-full.text-token-text-primary')
            if message_blocks and len(message_blocks) >= 2:
                last_block = message_blocks[-1]  # The last block is likely the assistant's response
                images = last_block.find_elements(By.TAG_NAME, 'img')
                
                if images:
                    # Try to take a screenshot of the first image in the response
                    try:
                        # Scroll to the image
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", images[0])
                        time.sleep(1)
                        
                        # Take screenshot of the image
                        output_file = os.path.join(directory_path, "output.png")
                        images[0].screenshot(output_file)
                        print(f"Image saved to {output_file} (method 1)")
                        return True
                    except Exception as e1:
                        print(f"Error capturing image with method 1: {str(e1)}")
            
            # 2. Look for all images and try to find the generated one
            all_images = self.driver.find_elements(By.CSS_SELECTOR, 'img')
            if len(all_images) >= 2:  # At least 2 images (user uploaded + generated)
                # Skip the first image (usually the user uploaded one)
                for i, img in enumerate(all_images):
                    if i == 0:  # Skip the first image (user uploaded)
                        continue
                        
                    try:
                        # Check if it's likely a generated image
                        src = img.get_attribute('src')
                        if not src or 'avatar' in src.lower():
                            continue  # Skip profile avatars
                            
                        # Make sure the image is visible and has reasonable size
                        size = img.size
                        if size['width'] < 100 or size['height'] < 100:
                            continue  # Too small to be a generated image
                            
                        # Scroll to the image
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                        time.sleep(1)
                        
                        # Take screenshot of the image
                        output_file = os.path.join(directory_path, "output.png")
                        img.screenshot(output_file)
                        print(f"Image saved to {output_file} (method 2)")
                        return True
                    except Exception as e2:
                        print(f"Error capturing image {i} with method 2: {str(e2)}")
            
            # 3. Try using parent containers that might contain images
            image_containers = self.driver.find_elements(By.CSS_SELECTOR, '.flex.justify-center')
            for container in image_containers:
                try:
                    images = container.find_elements(By.TAG_NAME, 'img')
                    if images:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", images[0])
                        time.sleep(1)
                        
                        output_file = os.path.join(directory_path, "output.png")
                        images[0].screenshot(output_file)
                        print(f"Image saved to {output_file} (method 3)")
                        return True
                except Exception as e3:
                    print(f"Error with container method: {str(e3)}")
            
            # 4. Try to find image download button and get the URL
            download_buttons = self.driver.find_elements(By.XPATH, 
                '//button[contains(@aria-label, "Download") or contains(., "Download")]')
            
            if download_buttons:
                try:
                    # Try to get the image URL from the download button
                    button = download_buttons[0]
                    parent = button
                    
                    # Try to navigate up to find an image
                    for _ in range(5):  # Look up to 5 levels up
                        try:
                            parent = parent.find_element(By.XPATH, '..')
                            images = parent.find_elements(By.TAG_NAME, 'img')
                            if images:
                                output_file = os.path.join(directory_path, "output.png")
                                images[0].screenshot(output_file)
                                print(f"Image saved to {output_file} (method 4)")
                                return True
                        except:
                            break
                            
                except Exception as e4:
                    print(f"Error with download button method: {str(e4)}")
            
            print("Could not find and save the generated image with any method")
            return False
            
        except Exception as e:
            print(f"Error in find_and_save_generated_image: {str(e)}")
            traceback.print_exc()
            return False


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