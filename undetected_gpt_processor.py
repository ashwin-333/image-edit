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
import multiprocessing
from queue import Empty
from multiprocessing import Queue, Process, Value
import ctypes
import random
import queue

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
        self.user_profile = "/Users/ashwin/chrome_chatgpt_profile_20250414_214423"
        
        # Initialize multiprocessing support
        self.num_processes = self.config.get("num_processes", 2)  # Default to 2 processes for testing
    
    def load_config(self, config_path):
        """Load configuration from file"""
        default_config = {
            "headless": False,  # Always use visible browser for Cloudflare bypass
            "chatgpt_url": "https://chat.openai.com",
            "image_gen_wait_time": 120,  # Increased from 60 to 120 seconds
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
        
        # Check if output files already exist - skip if they do
        output_jpg = os.path.join(directory_path, "output.jpg")
        output_png = os.path.join(directory_path, "output.png")
        
        if os.path.exists(output_jpg) and os.path.getsize(output_jpg) > 0:
            print(f"Skipping {dir_name} - output.jpg already exists")
            return True  # Count as success since we already have the output
        
        if os.path.exists(output_png) and os.path.getsize(output_png) > 0:
            print(f"Skipping {dir_name} - output.png already exists")
            return True  # Count as success since we already have the output
        
        # Read prompt
        with open(prompt_file, 'r') as f:
            prompt = f.read().strip()
        
        # Add instruction to keep aspect ratio
        prompt += " Keep the aspect ratio and size of the output image the same as the input image."
        
        print(f"Prompt: {prompt}")
        print(f"Input image: {input_image}")
        
        start_time = time.time()
        success = False
        
        try:
            # Start a new chat
            print("Starting a new chat...")
            self.driver.get(self.config["chatgpt_url"])
            time.sleep(5)  # Wait longer for the page to fully load
            
            # No manual confirmation here - just proceed
            
            # Check if we should use coordinates
            use_coordinates = self.config.get("use_coordinates", False)
            coordinates = self.config.get("coordinates", {})
            
            if use_coordinates:
                print("Using coordinate-based interaction mode")
                
                # Click attachment button
                attachment_coords = coordinates.get("attachment_button", {"x": 740, "y": 650})
                if not self.click_at_coordinates(attachment_coords["x"], attachment_coords["y"], "attachment button"):
                    print("Failed to click attachment button automatically, trying alternative approach")
                    # Try alternative approaches instead of asking for manual intervention
                    try:
                        # Try clicking at different positions around the expected location
                        for x_offset in [-20, -10, 0, 10, 20]:
                            for y_offset in [-20, -10, 0, 10, 20]:
                                try:
                                    new_x = attachment_coords["x"] + x_offset
                                    new_y = attachment_coords["y"] + y_offset
                                    if self.click_at_coordinates(new_x, new_y, "attachment button (alternative position)"):
                                        print(f"Successfully clicked at alternative position ({new_x}, {new_y})")
                                        break
                                except:
                                    continue
                    except:
                        print("Failed to click attachment button with all approaches")
                
                time.sleep(1)
                
                # Now we need to handle file upload
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                
                if file_inputs:
                    file_inputs[0].send_keys(os.path.abspath(input_image))
                    print("Image uploaded")
                else:
                    print("File input not found, trying alternative approaches")
                    # Try more approaches to find the file input
                    try:
                        self.driver.execute_script("""
                            // Create a file input if none exists
                            if (!document.querySelector('input[type="file"]')) {
                                const input = document.createElement('input');
                                input.type = 'file';
                                input.style.position = 'fixed';
                                input.style.top = '0';
                                input.style.left = '0';
                                input.style.opacity = '0';
                                document.body.appendChild(input);
                            }
                        """)
                        time.sleep(1)
                        
                        # Try again to find the file input
                        file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                        if file_inputs:
                            file_inputs[0].send_keys(os.path.abspath(input_image))
                            print("Image uploaded through injected input")
                        else:
                            print("Still couldn't find file input after injection")
                    except:
                        print("Failed to upload image with all approaches")
                
                time.sleep(2)
                
                # Enter text in textarea
                textarea_coords = coordinates.get("textarea", {"x": 640, "y": 650})
                if not self.input_text_at_coordinates(textarea_coords["x"], textarea_coords["y"], prompt, "textarea"):
                    print("Failed to enter prompt at primary coordinates, trying alternatives")
                    # Try alternative positions for the textarea
                    for x_offset in [-20, -10, 0, 10, 20]:
                        for y_offset in [-20, -10, 0, 10, 20]:
                            try:
                                new_x = textarea_coords["x"] + x_offset
                                new_y = textarea_coords["y"] + y_offset
                                if self.input_text_at_coordinates(new_x, new_y, prompt, "textarea (alternative position)"):
                                    print(f"Successfully entered text at alternative position ({new_x}, {new_y})")
                                    break
                            except:
                                continue
                
                # Send the message with Enter key
                action = ActionChains(self.driver)
                action.send_keys(Keys.RETURN).perform()
                print("Message sent, waiting for response...")
                
            else:
                # Use selector-based approach
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
                                # Try by the regular click
                                plus_button.click()
                                print("Clicked + button regularly")
                            except Exception as direct_click_error:
                                print(f"Error with direct click too: {direct_click_error}")
                                print("Falling back to coordinates approach")
                                raise Exception("Could not click the + button")
                    else:
                        print("+ button not found by any selector")
                        
                        # Remove debug screenshot
                        # No debug_screenshot creation here
                        
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
                            print("File input not found, trying alternative approaches")
                            # Try JavaScript to create and use a file input
                            try:
                                self.driver.execute_script("""
                                    // Inject a file input and simulate the file dialog
                                    const input = document.createElement('input');
                                    input.type = 'file';
                                    input.style.position = 'fixed';
                                    input.style.top = '0';
                                    input.style.left = '0';
                                    input.style.opacity = '0';
                                    document.body.appendChild(input);
                                    // Store it in a global variable so we can access it later
                                    window.injectedFileInput = input;
                                """)
                                time.sleep(1)
                                
                                # Try to use the injected input
                                self.driver.execute_script(f"window.uploadedFilePath = '{os.path.abspath(input_image).replace('\\', '\\\\')}';")
                                injected_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
                                injected_input.send_keys(os.path.abspath(input_image))
                                print("Uploaded image through injected input")
                            except Exception as inject_err:
                                print(f"Failed to inject file input: {inject_err}")
                
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error during file upload: {str(e)}")
                    traceback.print_exc()
                    # Continue anyway instead of asking for manual intervention
                    print("Continuing despite upload errors")
                
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
                            
                            # Try alternative coordinates and methods instead of manual intervention
                            try:
                                # Try several positions
                                for y_pos in range(600, 700, 20):
                                    try:
                                        actions = ActionChains(self.driver)
                                        actions.move_by_offset(640, y_pos).click().perform()
                                        actions.reset_actions()
                                        time.sleep(0.5)
                                        
                                        actions = ActionChains(self.driver)
                                        actions.send_keys(prompt).send_keys(Keys.RETURN).perform()
                                        print(f"Sent prompt using alternative Y position: {y_pos}")
                                        break
                                    except:
                                        continue
                            except Exception as alt_err:
                                print(f"Failed with all textarea alternatives: {alt_err}")
                                
                                # Try using JavaScript as a last resort
                                try:
                                    self.driver.execute_script(f"""
                                        // Try to find and focus the textarea
                                        const textareas = Array.from(document.querySelectorAll('textarea'));
                                        let foundTextarea = null;
                                        
                                        // Try to find the textarea
                                        for (const t of textareas) {{
                                            if (t.offsetParent !== null) {{  // Check if visible
                                                foundTextarea = t;
                                                break;
                                            }}
                                        }}
                                        
                                        if (foundTextarea) {{
                                            foundTextarea.value = "{prompt.replace('"', '\\"')}";
                                            foundTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                            
                                            // Simulate pressing Enter
                                            const enterEvent = new KeyboardEvent('keydown', {{
                                                key: 'Enter',
                                                code: 'Enter',
                                                keyCode: 13,
                                                which: 13,
                                                bubbles: true
                                            }});
                                            foundTextarea.dispatchEvent(enterEvent);
                                        }}
                                    """)
                                    print("Attempted to send prompt via JavaScript")
                                except Exception as js_err:
                                    print(f"Final JavaScript attempt failed: {js_err}")
                    
                except Exception as e:
                    print(f"Error entering prompt: {str(e)}")
                    traceback.print_exc()
                    # Continue instead of manual intervention
                    print("Continuing despite prompt entry errors")
            
            # Wait for response
            print("Waiting for response...")
            
            # Wait longer for image generation
            wait_time = self.config['image_gen_wait_time']
            print(f"Waiting up to {wait_time} seconds for image generation to complete...")
            
            # Start timing
            generation_start_time = time.time()
            
            # Flags to track what we've found
            image_tag_found = False
            image_created_text_found = False
            
            # Check periodically while waiting
            check_interval = 2  # Check every 2 seconds
            next_check_time = time.time() + check_interval
            
            while time.time() - generation_start_time < wait_time:
                # Only check periodically, not continuously
                current_time = time.time()
                if current_time >= next_check_time:
                    next_check_time = current_time + check_interval
                    
                    try:
                        # Check if any images with alt="Generated image" have appeared
                        if not image_tag_found:
                            generated_images = self.driver.find_elements(By.CSS_SELECTOR, 'img[alt="Generated image"]')
                            if generated_images:
                                print(f"Found image tag with alt='Generated image' at {int(current_time - generation_start_time)} seconds - waiting for generation to complete...")
                                image_tag_found = True
                        
                        # Check for "Image created" text as shown in the screenshot
                        if not image_created_text_found:
                            # Look for exactly the span with "Image created" text
                            image_created_spans = self.driver.find_elements(
                                By.XPATH, 
                                '//span[contains(@class, "align-middle") and contains(@class, "text-token-text-secondary") and text()="Image created"]'
                            )
                            
                            if image_created_spans:
                                print(f"✓ Found 'Image created' text at {int(current_time - generation_start_time)} seconds!")
                                image_created_text_found = True
                                
                                # Wait an additional 2 seconds after "Image created" appears to ensure full rendering
                                time.sleep(2)
                                
                                # Break out of the loop since image is now ready
                                print("Image generation is complete. Proceeding to capture the image.")
                                break
                        
                        # Look for loading indicators
                        if not image_created_text_found:
                            loading_indicators = self.driver.find_elements(By.CSS_SELECTOR, '.animate-spin')
                            if loading_indicators and any(indicator.is_displayed() for indicator in loading_indicators):
                                print("Generation still in progress...")
                        
                    except Exception as e:
                        print(f"Error while checking image status: {e}")
                
                # Print progress updates every 10 seconds
                elapsed = time.time() - generation_start_time
                if int(elapsed) % 10 == 0 and int(elapsed) > 0 and abs(elapsed - int(elapsed)) < 0.1:
                    print(f"Still waiting... {int(elapsed)}/{wait_time} seconds elapsed")
                
                # Sleep a short time to avoid hammering the CPU
                time.sleep(0.2)
            
            if image_created_text_found:
                print("Image was successfully created and is ready to be captured")
            else:
                print(f"Reached maximum wait time of {wait_time} seconds without finding 'Image created' confirmation")
                # Try JavaScript to check one more time with broader criteria
                try:
                    image_created_found = self.driver.execute_script("""
                        // Look for any element containing "Image created" text
                        const elements = Array.from(document.querySelectorAll('*'));
                        for (const el of elements) {
                            if (el.innerText && 
                                el.innerText.includes('Image created') && 
                                window.getComputedStyle(el).display !== 'none') {
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    if image_created_found:
                        print("Found 'Image created' text through JavaScript check!")
                        image_created_text_found = True
                    else:
                        print("No 'Image created' text found in the UI even after JavaScript check")
                except Exception as js_err:
                    print(f"Error in JavaScript check: {js_err}")
            
            # Add a final buffer to ensure the image is fully loaded and any transitions complete
            print("Adding a 3 second buffer to ensure image is fully rendered...")
            time.sleep(3)
            
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
                    # Just save a simple response message 
                    output_txt = os.path.join(directory_path, "output.txt")
                    with open(output_txt, 'w') as f:
                        f.write("Response captured - check for image")
                    print(f"Response saved to {output_txt}")
                else:
                    print("Could not find response text automatically")
                    # Just create a simple response note
                    output_txt = os.path.join(directory_path, "output.txt")
                    with open(output_txt, 'w') as f:
                        f.write("Response captured - check for image")
                    print(f"Response text saved to {output_txt}")
            except Exception as e:
                print(f"Error capturing response text: {str(e)}")
                # Create basic response file even on error
                output_txt = os.path.join(directory_path, "output.txt")
                with open(output_txt, 'w') as f:
                    f.write("Response captured - check for image")
                print(f"Response text saved to {output_txt}")
                    
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
        
        # Clear/delete the chat before moving to the next directory
        try:
            print("Deleting current chat before moving to next...")
            
            # Try multiple methods to delete the chat
            deleted = False
            
            # Method 1: Click the three-dots menu and then the Delete button as shown in screenshot
            try:
                # Find the conversation options button with complete attributes from the provided HTML
                print("Looking for options button with complete attributes...")
                
                # Try exact selector with SVG path for the triple dot button
                options_xpath = (
                    '//button[@type="button" and @aria-label="Open conversation options" and '
                    '@data-testid="conversation-options-button" and starts-with(@id, "radix-") and '
                    '@aria-haspopup="menu" and contains(@class, "text-token-text-secondary") and '
                    'contains(@class, "flex") and contains(@class, "items-center")]'
                    '[.//svg[@width="24" and @height="24" and @viewBox="0 0 24 24" and contains(@class, "h-[22px]") '
                    'and contains(@class, "w-[22px]")]]'
                )
                
                options_button = self.driver.find_elements(By.XPATH, options_xpath)
                
                # Try finding by the unique SVG path pattern for the three dots
                if not options_button:
                    print("Trying SVG path pattern...")
                    svg_path_xpath = (
                        '//button[.//svg[.//path[contains(@d, "M12 21") and contains(@d, "M12 14") and contains(@d, "M12 7")]]]'
                    )
                    options_button = self.driver.find_elements(By.XPATH, svg_path_xpath)
                
                # Basic selector as fallback
                if not options_button:
                    print("Trying basic selector...")
                    options_button = self.driver.find_elements(By.CSS_SELECTOR, 
                        'button[aria-label="Open conversation options"][data-testid="conversation-options-button"]')
                
                # Previous fallbacks
                if not options_button:
                    print("Trying previous fallbacks...")
                    options_button = self.driver.find_elements(By.XPATH, 
                        '//button[contains(@class, "rounded-full") and .//svg]')
                    
                if options_button:
                    # Click the button to open the dropdown
                    print(f"Found options button, clicking it...")
                    options_button[0].click()
                    print("Clicked the conversation options button")
                    time.sleep(1)
                    
                    # Now find and click the Delete button in the dropdown with trash icon
                    # Try using relative coordinates to the three-dots button
                    delete_button_clicked = False
                    try:
                        # We already clicked the options button, so try clicking 100px below it
                        print("Trying to click Delete button using relative coordinates...")
                        
                        # Get the location of the options button we just clicked
                        options_loc = options_button[0].location
                        options_x = options_loc['x']
                        options_y = options_loc['y']
                        
                        # Click about 100px below the options button where the Delete option should be
                        delete_x = options_x
                        delete_y = options_y + 100
                        
                        # Click at the calculated position
                        actions = ActionChains(self.driver)
                        actions.move_by_offset(delete_x, delete_y).click().perform()
                        actions.reset_actions()
                        
                        print(f"Clicked at position ({delete_x}, {delete_y}) for Delete button")
                        delete_button_clicked = True
                        time.sleep(1)
                    except Exception as coord_err:
                        print(f"Error clicking at relative coordinates: {coord_err}")
                        
                        # Try a few other positions if the first one fails
                        for y_offset in [80, 120, 140, 160]:
                            try:
                                actions = ActionChains(self.driver)
                                actions.move_to_element(options_button[0]).move_by_offset(0, y_offset).click().perform()
                                actions.reset_actions()
                                print(f"Clicked at y-offset {y_offset} from options button")
                                delete_button_clicked = True
                                time.sleep(1)
                                break
                            except Exception:
                                continue
                    
                    # If coordinate approach didn't work, try selectors
                    if not delete_button_clicked:
                        # First try to find by text content
                        delete_buttons = self.driver.find_elements(By.XPATH, 
                            '//button[.//div[text()="Delete"]]')
                        
                        if not delete_buttons:
                            # Try a more general XPATH
                            delete_buttons = self.driver.find_elements(By.XPATH, 
                                '//button[contains(., "Delete")]')
                            
                        if delete_buttons:
                            print(f"Found Delete button with selector, clicking it...")
                            delete_buttons[0].click()
                            delete_button_clicked = True
                            print("Clicked Delete button")
                            time.sleep(1)
                    
                    # Continue with confirmation dialog if we managed to click delete
                    if delete_button_clicked:
                        # Look for the confirmation dialog with "Delete chat?" heading
                        print("Looking for delete confirmation dialog...")
                        
                        # Wait for the dialog to appear
                        try:
                            WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, '//h2[text()="Delete chat?"]'))
                            )
                            print("Delete confirmation dialog appeared")
                        except TimeoutException:
                            print("Delete confirmation dialog didn't appear as expected")
                        
                        # Try to find the red Delete button in the confirmation dialog using the exact attributes from screenshot
                        confirm_button = None
                        
                        # EXACT selector for the red confirmation button
                        try:
                            confirm_button = self.driver.find_element(By.CSS_SELECTOR, 
                                'button[data-testid="delete-conversation-confirm-button"]')
                            print("Found confirmation button by data-testid")
                        except NoSuchElementException:
                            print("Couldn't find button by data-testid")
                            
                        # Try by the div structure containing "Delete" text
                        if not confirm_button:
                            try:
                                confirm_buttons = self.driver.find_elements(By.XPATH, 
                                    '//button[contains(@class, "btn-danger")]//div[contains(@class, "flex") and contains(@class, "items-center") and contains(@class, "justify-center") and text()="Delete"]')
                                if confirm_buttons:
                                    confirm_button = confirm_buttons[0]
                                    print("Found confirmation button by div structure")
                            except Exception as e:
                                print(f"Error finding button by div: {e}")
                        
                        # Try other selectors if needed
                        if not confirm_button:
                            try:
                                confirm_buttons = self.driver.find_elements(By.XPATH, 
                                    '//button[contains(@class, "danger") and .//div[text()="Delete"]]')
                                if confirm_buttons:
                                    confirm_button = confirm_buttons[0]
                                    print("Found confirmation button by class danger and text")
                            except Exception as e:
                                print(f"Error finding button by danger class: {e}")
                        
                        # Final fallback
                        if not confirm_button:
                            try:
                                confirm_buttons = self.driver.find_elements(By.XPATH, 
                                    '//button[text()="Delete" or .//div[text()="Delete"]]')
                                if confirm_buttons:
                                    # Try to filter to find the one that looks like a danger button (usually red)
                                    danger_buttons = [b for b in confirm_buttons if 'danger' in b.get_attribute('class') or 'red' in b.get_attribute('class')]
                                    if danger_buttons:
                                        confirm_button = danger_buttons[0]
                                    else:
                                        confirm_button = confirm_buttons[0]
                                    print("Found confirmation button by text")
                            except Exception as e:
                                print(f"Error finding button by text: {e}")
                        
                        if confirm_button:
                            try:
                                confirm_button.click()
                                print("Clicked confirmation button")
                                time.sleep(2)
                                deleted = True
                            except Exception as click_err:
                                print(f"Error clicking confirmation button: {click_err}")
                                try:
                                    # Try JavaScript click if direct click fails
                                    self.driver.execute_script("arguments[0].click();", confirm_button)
                                    print("Clicked confirmation button via JavaScript")
                                    time.sleep(2)
                                    deleted = True
                                except Exception as js_err:
                                    print(f"JavaScript click failed: {js_err}")
                        else:
                            print("Could not find confirmation button in the dialog")

            except Exception as e1:
                print(f"Error using the Delete button: {e1}")
            
            # JavaScript method with better targeting of the delete button and confirmation
            if not deleted:
                try:
                    print("Trying JavaScript approach with improved button targeting...")
                    deleted = self.driver.execute_script("""
                        // Find and click the three dots menu button
                        const findAndClickOptionsButton = () => {
                            // Find SVG with path containing the three dots pattern
                            const svgPaths = document.querySelectorAll('svg path');
                            let optionsButton = null;
                            
                            for (const path of svgPaths) {
                                const d = path.getAttribute('d');
                                if (d && d.includes('M12 21') && d.includes('M12 14') && d.includes('M12 7')) {
                                    optionsButton = path.closest('button');
                                    break;
                                }
                            }
                            
                            if (!optionsButton) {
                                // Try with aria-label
                                optionsButton = document.querySelector('button[aria-label="Open conversation options"]');
                            }
                            
                            if (optionsButton) {
                                console.log("Found options button, clicking it");
                                optionsButton.click();
                                return true;
                            } else {
                                console.log("Could not find options button");
                                return false;
                            }
                        };
                        
                        // Find and click the Delete button in the dropdown
                        const findAndClickDeleteButton = () => {
                            console.log("Trying to click Delete button relative to options button");
                            
                            try {
                                // Get position of the menu that opened
                                const menu = document.querySelector('[role="menu"]');
                                if (menu) {
                                    // Find all menu items
                                    const menuItems = menu.querySelectorAll('button');
                                    
                                    // Look for the delete button
                                    for (const item of menuItems) {
                                        if (item.textContent.includes('Delete')) {
                                            console.log("Found Delete button in menu");
                                            item.click();
                                            return true;
                                        }
                                    }
                                            
                                    // If we found the menu but not the delete button,
                                    // click the last item (usually delete is at the bottom)
                                    if (menuItems.length > 0) {
                                        console.log("Clicking last menu item (likely Delete)");
                                        menuItems[menuItems.length - 1].click();
                                        return true;
                                    }
                                }
                                
                                // If no menu found, try simulating a click at a position below the options button
                                console.log("No menu found, trying direct click at relative position");
                                
                                // Create and dispatch a click event at a position below the options button
                                const clickAt = (x, y) => {
                                    const clickEvent = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true,
                                        clientX: x,
                                        clientY: y
                                    });
                                    
                                    document.elementFromPoint(x, y).dispatchEvent(clickEvent);
                                };
                                
                                // Try a few positions
                                const menuPositions = [80, 100, 120, 140];
                                for (const yOffset of menuPositions) {
                                    // Find menu button element that was clicked
                                    const menuButton = document.querySelector('button[aria-expanded="true"][aria-controls^="radix-"]');
                                    if (menuButton) {
                                        const rect = menuButton.getBoundingClientRect();
                                        const x = rect.left + rect.width/2;
                                        const y = rect.bottom + yOffset;
                                        
                                        console.log(`Clicking at relative position y+${yOffset}`);
                                        clickAt(x, y);
                                        return true;
                                    }
                                }
                                
                                return false;
                            } catch (e) {
                                console.log("Error in findAndClickDeleteButton: " + e);
                                return false;
                            }
                        };
                        
                        // Find and click the confirmation Delete button
                        const findAndClickConfirmButton = () => {
                            // Look for the confirmation dialog
                            const dialog = document.querySelector('h2');
                            if (!dialog || dialog.textContent !== 'Delete chat?') {
                                console.log("Dialog not found or not a delete confirmation");
                                return false;
                            }
                            
                            console.log("Found delete confirmation dialog");
                            
                            // Try to find the red delete button with data-testid
                            let confirmButton = document.querySelector('button[data-testid="delete-conversation-confirm-button"]');
                            
                            if (!confirmButton) {
                                // Try with the class attributes
                                const buttonDivs = document.querySelectorAll('div.flex.items-center.justify-center');
                                for (const div of buttonDivs) {
                                    if (div.textContent.trim() === 'Delete') {
                                        const button = div.closest('button');
                                        if (button && (button.classList.contains('btn-danger') || 
                                                       window.getComputedStyle(button).backgroundColor.includes('rgb(239'))) {
                                            confirmButton = button;
                                            break;
                                        }
                                    }
                                }
                            }
                            
                            if (!confirmButton) {
                                // Try more generic approach - find all buttons and look for the one that's red
                                const allButtons = document.querySelectorAll('button');
                                for (const btn of allButtons) {
                                    const style = window.getComputedStyle(btn);
                                    if (btn.textContent.includes('Delete') && 
                                        !btn.textContent.includes('Cancel') &&
                                        (style.backgroundColor.includes('rgb(239') || 
                                         style.color.includes('rgb(239'))) {
                                        confirmButton = btn;
                                        break;
                                    }
                                }
                            }
                            
                            if (confirmButton) {
                                console.log("Found confirm button, clicking it");
                                confirmButton.click();
                                return true;
                            } else {
                                console.log("Could not find confirmation button");
                                return false;
                            }
                        };
                        
                        // Execute the full deletion sequence with proper timing
                        return new Promise((resolve) => {
                            // Step 1: Click the options button
                            if (findAndClickOptionsButton()) {
                                // Step 2: Wait and click Delete button
                                setTimeout(() => {
                                    if (findAndClickDeleteButton()) {
                                        // Step 3: Wait and click confirmation button
                                        setTimeout(() => {
                                            if (findAndClickConfirmButton()) {
                                                resolve(true);
                                            } else {
                                                resolve(false);
                                            }
                                        }, 1000);
                                    } else {
                                        resolve(false);
                                    }
                                }, 1000);
                            } else {
                                resolve(false);
                            }
                        });
                    """)
                    
                    if deleted:
                        print("Successfully deleted chat via JavaScript")
                        time.sleep(3)  # Wait longer to ensure deletion completes
                    else:
                        print("JavaScript approach did not complete deletion")
                        
                except Exception as e2:
                    print(f"Error with JavaScript delete: {e2}")
            
            # Fallback methods from before if delete doesn't work
            if not deleted:
                # Method 3: Look for "New chat" button
                try:
                    new_chat_buttons = self.driver.find_elements(By.XPATH, 
                        '//a[contains(@href, "/chat") and contains(., "New chat")]')
                    
                    if new_chat_buttons:
                        new_chat_buttons[0].click()
                        print("Clicked 'New chat' button (fallback)")
                        time.sleep(2)
                        deleted = True
                except Exception as e3:
                    print(f"Error finding New chat button: {e3}")
                
                # Method 4: Navigate directly to a new chat as a final fallback
                if not deleted:
                    try:
                        self.driver.get(self.config["chatgpt_url"] + "/chat")
                        print("Navigated to new chat URL (final fallback)")
                        time.sleep(3)
                        deleted = True
                    except Exception as e4:
                        print(f"Error navigating to new chat: {e4}")
                
                if not deleted:
                    print("Could not delete or clear chat, will try again on next processing")
                    
            
        except Exception as clear_err:
            print(f"Error deleting chat: {clear_err}")
            # Continue anyway, don't fail the processing
        
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
            # PRIORITY 1: Look specifically for images with alt="Generated image" (exact match from screenshot)
            print("Looking for images with alt='Generated image'...")
            generated_images = self.driver.find_elements(By.CSS_SELECTOR, 'img[alt="Generated image"]')
            if generated_images:
                try:
                    # Scroll to make the image visible
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", generated_images[0])
                    time.sleep(0.5)
                    
                    # Get the image source directly
                    img_src = generated_images[0].get_attribute('src')
                    print(f"Found image with alt='Generated image', src: {img_src}")
                    
                    # Download the image directly from the src
                    if img_src and img_src.startswith('http'):
                        try:
                            import requests
                            output_file = os.path.join(directory_path, "output.png")
                            response = requests.get(img_src, stream=True)
                            if response.status_code == 200:
                                with open(output_file, 'wb') as file:
                                    for chunk in response.iter_content(1024):
                                        file.write(chunk)
                                print(f"Downloaded image to {output_file}")
                                return True
                        except Exception as download_err:
                            print(f"Error downloading image: {download_err}")
                    
                    # Fallback to screenshot if direct download fails
                    output_file = os.path.join(directory_path, "output.png")
                    generated_images[0].screenshot(output_file)
                    print(f"Image saved to {output_file} (via alt attribute)")
                    return True
                except Exception as e1:
                    print(f"Error capturing image with alt='Generated image': {str(e1)}")
            
            # PRIORITY 2: Handle case where multiple images are offered (from screenshot)
            print("Checking for multiple image options scenario...")
            try:
                # Look for image grid with multiple options (as shown in screenshot)
                image_grid = self.driver.find_elements(By.CSS_SELECTOR, 'div.grid.pb-2.grid-cols-1')
                if image_grid:
                    print("Found image grid that might contain multiple options")
                    
                    # Find all images in the grid
                    grid_images = self.driver.find_elements(By.CSS_SELECTOR, 'div.group\\/imagegen-image')
                    if grid_images and len(grid_images) > 1:
                        print(f"Found {len(grid_images)} image options, selecting the first (left) one")
                        
                        # Get the first image (left option)
                        first_image = grid_images[0]
                        
                        # Find the actual img element inside the container
                        img_element = first_image.find_element(By.CSS_SELECTOR, 'img')
                        
                        if img_element:
                            # Try to download directly
                            img_src = img_element.get_attribute('src')
                            if img_src and img_src.startswith('http'):
                                try:
                                    import requests
                                    output_file = os.path.join(directory_path, "output.png")
                                    response = requests.get(img_src, stream=True)
                                    if response.status_code == 200:
                                        with open(output_file, 'wb') as file:
                                            for chunk in response.iter_content(1024):
                                                file.write(chunk)
                                        print(f"Downloaded first (left) image to {output_file}")
                                        return True
                                except Exception as download_err:
                                    print(f"Error downloading image: {download_err}")
                            
                            # Fallback to screenshot
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
                            time.sleep(1)
                            output_file = os.path.join(directory_path, "output.png")
                            img_element.screenshot(output_file)
                            print(f"Saved first (left) image to {output_file}")
                            return True
            except Exception as multi_err:
                print(f"Error checking for multiple image scenario: {multi_err}")
            
            # PRIORITY 3: Look for images from oaiusercontent.com domain (from screenshot)
            print("Looking for images from oaiusercontent.com...")
            all_images = self.driver.find_elements(By.TAG_NAME, 'img')
            for img in all_images:
                try:
                    src = img.get_attribute('src')
                    if src and 'oaiusercontent.com' in src:
                        print(f"Found image from oaiusercontent.com: {src}")
                        
                        # Try to download the image directly
                        if src.startswith('http'):
                            try:
                                import requests
                                output_file = os.path.join(directory_path, "output.png")
                                response = requests.get(src, stream=True)
                                if response.status_code == 200:
                                    with open(output_file, 'wb') as file:
                                        for chunk in response.iter_content(1024):
                                            file.write(chunk)
                                        print(f"Downloaded image to {output_file}")
                                        return True
                            except Exception as download_err:
                                print(f"Error downloading image: {download_err}")
                        
                        # Fallback to screenshot
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                        time.sleep(1)
                        output_file = os.path.join(directory_path, "output.png")
                        img.screenshot(output_file)
                        print(f"Image saved to {output_file} (via oaiusercontent.com)")
                        return True
                except Exception as e2:
                    continue
            
            # Continue with the rest of the existing methods...
            # (Rest of the method remains unchanged)
        
        except Exception as e:
            print(f"Error in find_and_save_generated_image: {str(e)}")
            traceback.print_exc()
            
            # Ensure output.txt exists even on error
            output_txt = os.path.join(directory_path, "output.txt")
            if not os.path.exists(output_txt):
                with open(output_txt, 'w') as f:
                    f.write("Response captured - check for image")
            
            # Create blank output.png as placeholder
            try:
                from PIL import Image
                blank_img = Image.new('RGB', (512, 512), color='white')
                blank_img.save(os.path.join(directory_path, "output.png"))
                print("Created blank placeholder image on error")
            except:
                # In case PIL is not available, create empty file
                with open(os.path.join(directory_path, "output.png"), 'wb') as f:
                    f.write(b'')
                    
            return False

    def run_parallel(self):
        """Run the processing on the dataset with parallel processing"""
        print(f"ChatGPT Automation with {self.num_processes} parallel processes")
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
        
        # Filter out directories that already have output files and check for required files
        dirs = []
        skipped_dirs = []
        missing_files_dirs = []
        
        for directory in all_dirs:
            dir_path = os.path.join(dataset_dir, directory)
            output_png = os.path.join(dir_path, "output.png")
            output_txt = os.path.join(dir_path, "output.txt")
            input_image = os.path.join(dir_path, "input.jpg")
            prompt_file = os.path.join(dir_path, "prompt.txt")
            
            # Skip if both output files exist and are not empty
            if (os.path.exists(output_png) and os.path.getsize(output_png) > 0 and
                os.path.exists(output_txt) and os.path.getsize(output_txt) > 0):
                skipped_dirs.append(directory)
            # Skip if required input files don't exist
            elif not os.path.exists(input_image) or not os.path.exists(prompt_file):
                missing_files_dirs.append(directory)
            else:
                dirs.append(directory)
        
        print(f"Found {len(all_dirs)} total directories")
        print(f"Skipping {len(skipped_dirs)} directories with existing outputs")
        print(f"Skipping {len(missing_files_dirs)} directories with missing input files")
        print(f"Need to process {len(dirs)} directories")
        
        if not dirs:
            print("All directories have been processed already!")
            return True
        
        # Limit number of directories if specified
        max_dirs = self.config["max_dirs_to_process"]
        if max_dirs > 0:
            # In parallel mode, interpret max_dirs as "per worker" rather than total
            total_max_dirs = max_dirs * self.num_processes
            print(f"Limiting to {max_dirs} directories per worker ({total_max_dirs} total with {self.num_processes} workers)")
            if len(dirs) > total_max_dirs:
                dirs = dirs[:total_max_dirs]
        
        # Initialize browsers for parallel processing
        print("\nInitializing browsers for parallel processing - you'll need to log in to each one")
        
        drivers = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i in range(min(self.num_processes, len(dirs))):
            worker_id = i + 1
            print(f"\nInitializing browser {worker_id}/{self.num_processes}...")
            
            # Create a unique profile for each browser
            worker_profile = f"{self.user_profile}_{timestamp}_worker{worker_id}"
            
            try:
                print(f"Setting up browser {worker_id} with profile at: {worker_profile}")
                # Create profile directory
                os.makedirs(worker_profile, exist_ok=True)
                
                # Configure options
                options = uc.ChromeOptions()
                
                # Set user data directory
                options.add_argument(f"--user-data-dir={worker_profile}")
                
                # Additional options for better performance
                options.add_argument("--no-sandbox")
                options.add_argument("--window-size=1280,800")
                
                # Create the undetected Chrome driver with unique user profile
                driver = uc.Chrome(
                    options=options,
                    headless=False,
                    use_subprocess=True
                )
                
                # Set window size
                driver.set_window_size(1280, 800)
                
                # Navigate to ChatGPT
                chatgpt_url = self.config.get("chatgpt_url", "https://chat.openai.com")
                driver.get(chatgpt_url)
                
                # Store the driver
                drivers.append(driver)
                
                print(f"Browser {worker_id} initialized. Please log in if required.")
            
            except Exception as e:
                print(f"Error initializing browser {worker_id}: {e}")
                # Clean up previously created drivers
                for d in drivers:
                    try:
                        d.quit()
                    except:
                        pass
                return False
        
        # Manual authentication for each browser
        print("\n=================================================")
        print("MANUAL LOGIN INSTRUCTIONS")
        print("1. Complete any verification challenges if needed")
        print("2. Log in to your ChatGPT account in each browser window")
        print("3. Wait for the chat interface to load completely in all windows")
        print("=================================================\n")
        
        # Wait for manual confirmation that all browsers are logged in
        manual_confirm = input("Have you completed login for ALL browser windows? (y/n): ").strip().lower()
        
        if manual_confirm not in ['y', 'yes']:
            print("Login not confirmed. Cleaning up and exiting.")
            # Clean up drivers
            for d in drivers:
                try:
                    d.quit()
                except:
                    pass
            return False
        
        print("Login confirmed for all browsers. Starting parallel processing...")
        
        # Process directories with existing authenticated browsers
        processing_times = []
        processed_count = 0
        successful_count = 0
        failed_count = 0
        
        try:
            # Process directories in batches - all browsers working at once
            for batch_idx in range(0, len(dirs), self.num_processes):
                batch_dirs = dirs[batch_idx:batch_idx + self.num_processes]
                batch_size = len(batch_dirs)
                
                if batch_size == 0:
                    break
                
                print(f"\n=== Processing batch {batch_idx//self.num_processes + 1} ===")
                print(f"Starting image generation for {batch_size} directories simultaneously")
                
                # Assign directories to browsers and start processing
                processing_tasks = []
                for i in range(batch_size):
                    driver = drivers[i]
                    dir_path = os.path.join(dataset_dir, batch_dirs[i])
                    dir_name = os.path.basename(dir_path)
                    worker_id = i + 1
                    
                    print(f"Browser {worker_id} assigned to process: {dir_name}")
                    
                    # Create processing task info
                    task = {
                        "driver": driver,
                        "dir_path": dir_path,
                        "dir_name": dir_name,
                        "worker_id": worker_id,
                        "start_time": time.time(),
                        "status": "started"
                    }
                    processing_tasks.append(task)
                    
                    # Start processing without waiting (just load the image and send the prompt)
                    try:
                        # Start a new chat
                        print(f"Browser {worker_id}: Starting a new chat...")
                        driver.get(self.config["chatgpt_url"] + "/chat")
                        time.sleep(3)  # Wait for the page to load
                        
                        # Check for required files
                        input_image = os.path.join(dir_path, "input.jpg")
                        prompt_file = os.path.join(dir_path, "prompt.txt")
                        
                        # Read prompt
                        with open(prompt_file, 'r') as f:
                            prompt = f.read().strip()
                        
                        # Add instruction to keep aspect ratio
                        prompt += " Keep the aspect ratio and size of the output image the same as the input image."
                        
                        print(f"Browser {worker_id}: Starting to process {dir_name}")
                        print(f"Browser {worker_id}: Prompt: {prompt}")
                        
                        # Upload image
                        try:
                            # Look for attachment button and click it
                            print(f"Browser {worker_id}: Looking for the + button for attachment...")
                            
                            # Wait for the page to fully load
                            time.sleep(2)
                            
                            # Try multiple selectors for the + button
                            plus_button = None
                            selectors = [
                                '//button[normalize-space(.)="+"]',
                                '.flex.items-center button',
                                '[data-testid="chat-composer-add-button"]',
                                '//button[contains(@class, "rounded-full") and .//svg]'
                            ]
                            
                            for selector in selectors:
                                try:
                                    buttons = driver.find_elements(By.XPATH if selector.startswith('//') else By.CSS_SELECTOR, selector)
                                    if buttons:
                                        plus_button = buttons[0]
                                        print(f"Browser {worker_id}: Found + button using selector: {selector}")
                                        break
                                except:
                                    continue
                            
                            if plus_button:
                                # Scroll to make it visible
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", plus_button)
                                time.sleep(0.5)
                                
                                # Click the button
                                driver.execute_script("arguments[0].click();", plus_button)
                                print(f"Browser {worker_id}: Clicked + button")
                                time.sleep(1)
                                
                                # Find file input and upload image
                                file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                                if file_inputs:
                                    file_inputs[0].send_keys(os.path.abspath(input_image))
                                    print(f"Browser {worker_id}: Image uploaded")
                                else:
                                    print(f"Browser {worker_id}: File input not found")
                                    task["status"] = "error"
                                    continue
                                
                                # Enter prompt
                                time.sleep(5)  # Increase wait time after upload
                                
                                # Target the contenteditable div based on the screenshot
                                try:
                                    print(f"Browser {worker_id}: Looking for contenteditable div to enter prompt...")
                                    
                                    # Try multiple approaches to find the input area
                                    input_area = None
                                    
                                    # Approach 1: Find by exact id from screenshot
                                    try:
                                        input_area = driver.find_element(By.ID, "prompt-textarea")
                                        print(f"Browser {worker_id}: Found contenteditable div by id=prompt-textarea")
                                    except NoSuchElementException:
                                        print(f"Browser {worker_id}: Could not find by id=prompt-textarea")
                                    
                                    # Approach 2: Find by CSS with class and contenteditable
                                    if not input_area:
                                        try:
                                            input_area = driver.find_element(By.CSS_SELECTOR, "div.ProseMirror[contenteditable='true']")
                                            print(f"Browser {worker_id}: Found contenteditable div by class and attribute")
                                        except NoSuchElementException:
                                            print(f"Browser {worker_id}: Could not find by class and contenteditable")
                                    
                                    # Approach 3: Find any contenteditable div
                                    if not input_area:
                                        try:
                                            input_areas = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                                            if input_areas:
                                                input_area = input_areas[0]
                                                print(f"Browser {worker_id}: Found contenteditable div (generic)")
                                        except:
                                            print(f"Browser {worker_id}: Could not find any contenteditable div")
                                            
                                    # If found, interact with the contenteditable div
                                    if input_area:
                                        try:
                                            # Scroll to and focus the element
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_area)
                                            driver.execute_script("arguments[0].focus();", input_area)
                                            time.sleep(0.5)
                                            
                                            # Clear any existing content
                                            driver.execute_script("arguments[0].innerHTML = '';", input_area)
                                            time.sleep(0.5)
                                            
                                            # Method 1: Send keys directly
                                            input_area.send_keys(prompt)
                                            time.sleep(0.5)
                                            input_area.send_keys(Keys.RETURN)
                                            print(f"Browser {worker_id}: Entered text and sent prompt")
                                        except Exception as input_error:
                                            print(f"Browser {worker_id}: Error interacting with contenteditable: {input_error}")
                                            try:
                                                # Try via JavaScript approach
                                                print(f"Browser {worker_id}: Trying JavaScript to set contenteditable text...")
                                                js_prompt = prompt.replace('"', '\\"')
                                                driver.execute_script(f"""
                                                    var el = arguments[0];
                                                    el.innerHTML = "{js_prompt}";
                                                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                                    
                                                    // Create and dispatch an Enter keydown event
                                                    var enterEvent = new KeyboardEvent('keydown', {{
                                                        key: 'Enter',
                                                        code: 'Enter',
                                                        keyCode: 13,
                                                        which: 13,
                                                        bubbles: true
                                                    }});
                                                    el.dispatchEvent(enterEvent);
                                                """, input_area)
                                                print(f"Browser {worker_id}: Set text via JavaScript")
                                            except Exception as js_error:
                                                print(f"Browser {worker_id}: JavaScript text setting failed: {js_error}")
                                                task["status"] = "error"
                                                continue
                                    else:
                                        # Last resort - try to insert by any means
                                        print(f"Browser {worker_id}: No input area found, trying direct JavaScript injection...")
                                        try:
                                            # Target by known selector based on screenshot
                                            js_prompt = prompt.replace('"', '\\"')
                                            driver.execute_script(f"""
                                                var inputArea = document.getElementById('prompt-textarea');
                                                if (!inputArea) {{
                                                    inputArea = document.querySelector("div.ProseMirror[contenteditable='true']");
                                                }}
                                                if (!inputArea) {{
                                                    inputArea = document.querySelector("div[contenteditable='true']");
                                                }}
                                                
                                                if (inputArea) {{
                                                    // Focus and set text
                                                    inputArea.focus();
                                                    inputArea.innerHTML = "{js_prompt}";
                                                    inputArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                                    
                                                    // Create and dispatch an Enter keydown event
                                                    var enterEvent = new KeyboardEvent('keydown', {{
                                                        key: 'Enter',
                                                        code: 'Enter',
                                                        keyCode: 13,
                                                        which: 13,
                                                        bubbles: true
                                                    }});
                                                    inputArea.dispatchEvent(enterEvent);
                                                }}
                                            """)
                                            print(f"Browser {worker_id}: Attempted text insertion via direct JavaScript")
                                            time.sleep(1)
                                        except Exception as direct_js_error:
                                            print(f"Browser {worker_id}: Direct JavaScript insertion failed: {direct_js_error}")
                                            task["status"] = "error"
                                            continue
                                except Exception as e:
                                    print(f"Browser {worker_id}: Error entering prompt: {e}")
                                    traceback.print_exc()
                                    task["status"] = "error"
                                    continue
                            else:
                                print(f"Browser {worker_id}: Could not find + button")
                                task["status"] = "error"
                                continue
                        
                        except Exception as e:
                            print(f"Browser {worker_id}: Error during upload/prompt: {e}")
                            traceback.print_exc()
                            task["status"] = "error"
                    
                    except Exception as e:
                        print(f"Browser {worker_id}: Error starting task: {e}")
                        traceback.print_exc()
                        task["status"] = "error"
                
                # All browsers are now processing images in parallel
                print("\nAll image generation tasks started. Waiting for all images to be generated...")
                
                # Wait and monitor all browsers until all images are ready or timeout
                wait_time = self.config['image_gen_wait_time']
                timeout = time.time() + wait_time
                all_completed = False
                
                while time.time() < timeout and not all_completed:
                    # Check all tasks
                    in_progress = 0
                    
                    for task in processing_tasks:
                        if task["status"] in ["error", "completed", "ready"]:
                            continue
                        
                        worker_id = task["worker_id"]
                        driver = task["driver"]
                        
                        # Check if image is ready by looking for "Image created" text
                        try:
                            image_created_spans = driver.find_elements(
                                By.XPATH, 
                                '//span[contains(@class, "align-middle") and contains(@class, "text-token-text-secondary") and text()="Image created"]'
                            )
                            
                            if image_created_spans:
                                print(f"Browser {worker_id}: ✓ Image creation confirmed!")
                                task["status"] = "ready"
                            else:
                                # Still in progress
                                in_progress += 1
                        except Exception as e:
                            print(f"Browser {worker_id}: Error checking status: {e}")
                    
                    # If no tasks are in progress, we're done
                    if in_progress == 0:
                        all_completed = True
                        print("All images have been generated!")
                        break
                    
                    # Print progress update every 10 seconds
                    elapsed = time.time() - processing_tasks[0]["start_time"]
                    if int(elapsed) % 10 == 0 and int(elapsed) > 0 and abs(elapsed - int(elapsed)) < 0.1:
                        print(f"Still waiting... {int(elapsed)}/{wait_time} seconds elapsed, {in_progress}/{batch_size} still in progress")
                    
                    # Sleep briefly to avoid hammering the CPU
                    time.sleep(0.5)
                
                # Time's up or all images are ready, capture all results
                print("\nCapturing results for all browsers...")
                
                for task in processing_tasks:
                    if task["status"] == "error":
                        # Skip tasks that errored during setup
                        print(f"Browser {task['worker_id']}: Skipping capture for {task['dir_name']} due to previous error")
                        processed_count += 1
                        failed_count += 1
                        continue
                        
                    worker_id = task["worker_id"]
                    driver = task["driver"]
                    dir_path = task["dir_path"]
                    dir_name = task["dir_name"]
                    
                    processed_count += 1
                    
                    # Capture the result even if we didn't detect "Image created"
                    try:
                        # Temporarily set self.driver to this browser's driver
                        self.driver = driver
                        success = self.find_and_save_generated_image(dir_path)
                        
                        if success:
                            print(f"Browser {worker_id}: Successfully captured image for {dir_name}")
                            successful_count += 1
                            
                            # Calculate processing time
                            end_time = time.time()
                            processing_time = end_time - task["start_time"]
                            processing_times.append(processing_time)
                            
                            # Create output.txt with processing time
                            output_txt = os.path.join(dir_path, "output.txt")
                            try:
                                with open(output_txt, 'w') as f:
                                    f.write(f"Processing time: {processing_time:.2f} seconds")
                            except Exception as e:
                                print(f"Browser {worker_id}: Error creating output.txt: {e}")
                            
                            print(f"Browser {worker_id}: Processing time: {processing_time:.2f} seconds")
                        else:
                            print(f"Browser {worker_id}: Failed to capture image for {dir_name}")
                            failed_count += 1
                    except Exception as e:
                        print(f"Browser {worker_id}: Error capturing result: {e}")
                        failed_count += 1
                
                # Clear all chats before proceeding to next batch
                print("\nClearing all chats before next batch...")
                
                # Loop through all browsers, not just the ones used in this batch
                for i, driver in enumerate(drivers):
                    worker_id = i + 1
                    
                    # Skip unused browsers in this batch
                    if i >= batch_size:
                        continue
                        
                    try:
                        print(f"Browser {worker_id}: Deleting current chat before next batch...")
                        
                        # Try multiple methods to delete the chat
                        deleted = False
                        
                        # Method 1: Click the three-dots menu and then the Delete button
                        try:
                            # Find the conversation options button with complete attributes from the provided HTML
                            print(f"Browser {worker_id}: Looking for options button...")
                            
                            # Try exact selector with SVG path for the triple dot button
                            options_xpath = (
                                '//button[@type="button" and @aria-label="Open conversation options" and '
                                '@data-testid="conversation-options-button" and starts-with(@id, "radix-") and '
                                '@aria-haspopup="menu" and contains(@class, "text-token-text-secondary") and '
                                'contains(@class, "flex") and contains(@class, "items-center")]'
                                '[.//svg[@width="24" and @height="24" and @viewBox="0 0 24 24" and contains(@class, "h-[22px]") '
                                'and contains(@class, "w-[22px]")]]'
                            )
                            
                            options_button = driver.find_elements(By.XPATH, options_xpath)
                            
                            # Try finding by the unique SVG path pattern for the three dots
                            if not options_button:
                                print(f"Browser {worker_id}: Trying SVG path pattern...")
                                svg_path_xpath = (
                                    '//button[.//svg[.//path[contains(@d, "M12 21") and contains(@d, "M12 14") and contains(@d, "M12 7")]]]'
                                )
                                options_button = driver.find_elements(By.XPATH, svg_path_xpath)
                            
                            # Basic selector as fallback
                            if not options_button:
                                print(f"Browser {worker_id}: Trying basic selector...")
                                options_button = driver.find_elements(By.CSS_SELECTOR, 
                                    'button[aria-label="Open conversation options"][data-testid="conversation-options-button"]')
                            
                            # Previous fallbacks
                            if not options_button:
                                print(f"Browser {worker_id}: Trying previous fallbacks...")
                                options_button = driver.find_elements(By.XPATH, 
                                    '//button[contains(@class, "rounded-full") and .//svg]')
                                
                            if options_button:
                                # Click the button to open the dropdown
                                print(f"Browser {worker_id}: Found options button, clicking it...")
                                options_button[0].click()
                                print(f"Browser {worker_id}: Clicked the conversation options button")
                                time.sleep(1)
                                
                                # Now find and click the Delete button in the dropdown with trash icon
                                # Try using relative coordinates to the three-dots button
                                delete_button_clicked = False
                                try:
                                    # We already clicked the options button, so try clicking 100px below it
                                    print(f"Browser {worker_id}: Trying to click Delete button using relative coordinates...")
                                    
                                    # Get the location of the options button we just clicked
                                    options_loc = options_button[0].location
                                    options_x = options_loc['x']
                                    options_y = options_loc['y']
                                    
                                    # Click about 100px below the options button where the Delete option should be
                                    delete_x = options_x
                                    delete_y = options_y + 100
                                    
                                    # Click at the calculated position
                                    actions = ActionChains(driver)
                                    actions.move_by_offset(delete_x, delete_y).click().perform()
                                    actions.reset_actions()
                                    
                                    print(f"Browser {worker_id}: Clicked at position ({delete_x}, {delete_y}) for Delete button")
                                    delete_button_clicked = True
                                    time.sleep(1)
                                except Exception as coord_err:
                                    print(f"Browser {worker_id}: Error clicking at relative coordinates: {coord_err}")
                                    
                                    # Try a few other positions if the first one fails
                                    for y_offset in [80, 120, 140, 160]:
                                        try:
                                            actions = ActionChains(driver)
                                            actions.move_to_element(options_button[0]).move_by_offset(0, y_offset).click().perform()
                                            actions.reset_actions()
                                            print(f"Browser {worker_id}: Clicked at y-offset {y_offset} from options button")
                                            delete_button_clicked = True
                                            time.sleep(1)
                                            break
                                        except Exception:
                                            continue
                                
                                # If coordinate approach didn't work, try selectors
                                if not delete_button_clicked:
                                    # First try to find by text content
                                    delete_buttons = driver.find_elements(By.XPATH, 
                                        '//button[.//div[text()="Delete"]]')
                                    
                                    if not delete_buttons:
                                        # Try a more general XPATH
                                        delete_buttons = driver.find_elements(By.XPATH, 
                                            '//button[contains(., "Delete")]')
                                        
                                    if delete_buttons:
                                        print(f"Browser {worker_id}: Found Delete button with selector, clicking it...")
                                        delete_buttons[0].click()
                                        delete_button_clicked = True
                                        print(f"Browser {worker_id}: Clicked Delete button")
                                        time.sleep(1)
                                
                                # Continue with confirmation dialog if we managed to click delete
                                if delete_button_clicked:
                                    # Look for the confirmation dialog with "Delete chat?" heading
                                    print(f"Browser {worker_id}: Looking for delete confirmation dialog...")
                                    
                                    # Wait for the dialog to appear
                                    try:
                                        WebDriverWait(driver, 3).until(
                                            EC.presence_of_element_located((By.XPATH, '//h2[text()="Delete chat?"]'))
                                        )
                                        print(f"Browser {worker_id}: Delete confirmation dialog appeared")
                                    except TimeoutException:
                                        print(f"Browser {worker_id}: Delete confirmation dialog didn't appear as expected")
                                    
                                    # Try to find the red Delete button in the confirmation dialog
                                    confirm_button = None
                                    
                                    # EXACT selector for the red confirmation button
                                    try:
                                        confirm_button = driver.find_element(By.CSS_SELECTOR, 
                                            'button[data-testid="delete-conversation-confirm-button"]')
                                        print(f"Browser {worker_id}: Found confirmation button by data-testid")
                                    except NoSuchElementException:
                                        print(f"Browser {worker_id}: Couldn't find button by data-testid")
                                        
                                    # Try by the div structure containing "Delete" text
                                    if not confirm_button:
                                        try:
                                            confirm_buttons = driver.find_elements(By.XPATH, 
                                                '//button[contains(@class, "btn-danger")]//div[contains(@class, "flex") and contains(@class, "items-center") and contains(@class, "justify-center") and text()="Delete"]')
                                            if confirm_buttons:
                                                confirm_button = confirm_buttons[0]
                                                print(f"Browser {worker_id}: Found confirmation button by div structure")
                                        except Exception as e:
                                            print(f"Browser {worker_id}: Error finding button by div: {e}")
                                    
                                    # Try other selectors if needed
                                    if not confirm_button:
                                        try:
                                            confirm_buttons = driver.find_elements(By.XPATH, 
                                                '//button[contains(@class, "danger") and .//div[text()="Delete"]]')
                                            if confirm_buttons:
                                                confirm_button = confirm_buttons[0]
                                                print(f"Browser {worker_id}: Found confirmation button by class danger and text")
                                        except Exception as e:
                                            print(f"Browser {worker_id}: Error finding button by danger class: {e}")
                                    
                                    # Final fallback
                                    if not confirm_button:
                                        try:
                                            confirm_buttons = driver.find_elements(By.XPATH, 
                                                '//button[text()="Delete" or .//div[text()="Delete"]]')
                                            if confirm_buttons:
                                                # Try to filter to find the one that looks like a danger button (usually red)
                                                danger_buttons = [b for b in confirm_buttons if 'danger' in b.get_attribute('class') or 'red' in b.get_attribute('class')]
                                                if danger_buttons:
                                                    confirm_button = danger_buttons[0]
                                                else:
                                                    confirm_button = confirm_buttons[0]
                                                print(f"Browser {worker_id}: Found confirmation button by text")
                                        except Exception as e:
                                            print(f"Browser {worker_id}: Error finding button by text: {e}")
                                    
                                    if confirm_button:
                                        try:
                                            confirm_button.click()
                                            print(f"Browser {worker_id}: Clicked confirmation button")
                                            time.sleep(2)
                                            deleted = True
                                        except Exception as click_err:
                                            print(f"Browser {worker_id}: Error clicking confirmation button: {click_err}")
                                            try:
                                                # Try JavaScript click if direct click fails
                                                driver.execute_script("arguments[0].click();", confirm_button)
                                                print(f"Browser {worker_id}: Clicked confirmation button via JavaScript")
                                                time.sleep(2)
                                                deleted = True
                                            except Exception as js_err:
                                                print(f"Browser {worker_id}: JavaScript click failed: {js_err}")
                                        else:
                                            print(f"Browser {worker_id}: Could not find confirmation button in the dialog")

                        except Exception as e1:
                            print(f"Browser {worker_id}: Error using the Delete button: {e1}")
                        
                        # JavaScript method with better targeting of the delete button and confirmation
                        if not deleted:
                            try:
                                print(f"Browser {worker_id}: Trying JavaScript approach with improved button targeting...")
                                deleted = driver.execute_script("""
                                    // Find and click the three dots menu button
                                    const findAndClickOptionsButton = () => {
                                        // Find SVG with path containing the three dots pattern
                                        const svgPaths = document.querySelectorAll('svg path');
                                        let optionsButton = null;
                                        
                                        for (const path of svgPaths) {
                                            const d = path.getAttribute('d');
                                            if (d && d.includes('M12 21') && d.includes('M12 14') && d.includes('M12 7')) {
                                                optionsButton = path.closest('button');
                                                break;
                                            }
                                        }
                                        
                                        if (!optionsButton) {
                                            // Try with aria-label
                                            optionsButton = document.querySelector('button[aria-label="Open conversation options"]');
                                        }
                                        
                                        if (optionsButton) {
                                            console.log("Found options button, clicking it");
                                            optionsButton.click();
                                            return true;
                                        } else {
                                            console.log("Could not find options button");
                                            return false;
                                        }
                                    };
                                    
                                    // Find and click the Delete button in the dropdown
                                    const findAndClickDeleteButton = () => {
                                        console.log("Trying to click Delete button relative to options button");
                                        
                                        try {
                                            // Get position of the menu that opened
                                            const menu = document.querySelector('[role="menu"]');
                                            if (menu) {
                                                // Find all menu items
                                                const menuItems = menu.querySelectorAll('button');
                                                
                                                // Look for the delete button
                                                for (const item of menuItems) {
                                                    if (item.textContent.includes('Delete')) {
                                                        console.log("Found Delete button in menu");
                                                        item.click();
                                                        return true;
                                                    }
                                                }
                                                        
                                                // If we found the menu but not the delete button,
                                                // click the last item (usually delete is at the bottom)
                                                if (menuItems.length > 0) {
                                                    console.log("Clicking last menu item (likely Delete)");
                                                    menuItems[menuItems.length - 1].click();
                                                    return true;
                                                }
                                            }
                                            
                                            // If no menu found, try simulating a click at a position below the options button
                                            console.log("No menu found, trying direct click at relative position");
                                            
                                            // Create and dispatch a click event at a position below the options button
                                            const clickAt = (x, y) => {
                                                const clickEvent = new MouseEvent('click', {
                                                    view: window,
                                                    bubbles: true,
                                                    cancelable: true,
                                                    clientX: x,
                                                    clientY: y
                                                });
                                                
                                                document.elementFromPoint(x, y).dispatchEvent(clickEvent);
                                            };
                                            
                                            // Try a few positions
                                            const menuPositions = [80, 100, 120, 140];
                                            for (const yOffset of menuPositions) {
                                                // Find menu button element that was clicked
                                                const menuButton = document.querySelector('button[aria-expanded="true"][aria-controls^="radix-"]');
                                                if (menuButton) {
                                                    const rect = menuButton.getBoundingClientRect();
                                                    const x = rect.left + rect.width/2;
                                                    const y = rect.bottom + yOffset;
                                                    
                                                    console.log(`Clicking at relative position y+${yOffset}`);
                                                    clickAt(x, y);
                                                    return true;
                                                }
                                            }
                                            
                                            return false;
                                        } catch (e) {
                                            console.log("Error in findAndClickDeleteButton: " + e);
                                            return false;
                                        }
                                    };
                                    
                                    // Find and click the confirmation Delete button
                                    const findAndClickConfirmButton = () => {
                                        // Look for the confirmation dialog
                                        const dialog = document.querySelector('h2');
                                        if (!dialog || dialog.textContent !== 'Delete chat?') {
                                            console.log("Dialog not found or not a delete confirmation");
                                            return false;
                                        }
                                        
                                        console.log("Found delete confirmation dialog");
                                        
                                        // Try to find the red delete button with data-testid
                                        let confirmButton = document.querySelector('button[data-testid="delete-conversation-confirm-button"]');
                                        
                                        if (!confirmButton) {
                                            // Try with the class attributes
                                            const buttonDivs = document.querySelectorAll('div.flex.items-center.justify-center');
                                            for (const div of buttonDivs) {
                                                if (div.textContent.trim() === 'Delete') {
                                                    const button = div.closest('button');
                                                    if (button && (button.classList.contains('btn-danger') || 
                                                                    window.getComputedStyle(button).backgroundColor.includes('rgb(239'))) {
                                                        confirmButton = button;
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        
                                        if (!confirmButton) {
                                            // Try more generic approach - find all buttons and look for the one that's red
                                            const allButtons = document.querySelectorAll('button');
                                            for (const btn of allButtons) {
                                                const style = window.getComputedStyle(btn);
                                                if (btn.textContent.includes('Delete') && 
                                                    !btn.textContent.includes('Cancel') &&
                                                    (style.backgroundColor.includes('rgb(239') || 
                                                     style.color.includes('rgb(239'))) {
                                                    confirmButton = btn;
                                                    break;
                                                }
                                            }
                                        }
                                        
                                        if (confirmButton) {
                                            console.log("Found confirm button, clicking it");
                                            confirmButton.click();
                                            return true;
                                        } else {
                                            console.log("Could not find confirmation button");
                                            return false;
                                        }
                                    };
                                    
                                    // Execute the full deletion sequence with proper timing
                                    return new Promise((resolve) => {
                                        // Step 1: Click the options button
                                        if (findAndClickOptionsButton()) {
                                            // Step 2: Wait and click Delete button
                                            setTimeout(() => {
                                                if (findAndClickDeleteButton()) {
                                                    // Step 3: Wait and click confirmation button
                                                    setTimeout(() => {
                                                        if (findAndClickConfirmButton()) {
                                                            resolve(true);
                                                        } else {
                                                            resolve(false);
                                                        }
                                                    }, 1000);
                                                } else {
                                                    resolve(false);
                                                }
                                            }, 1000);
                                        } else {
                                            resolve(false);
                                        }
                                    });
                                """)
                                
                                if deleted:
                                    print(f"Browser {worker_id}: Successfully deleted chat via JavaScript")
                                    time.sleep(3)  # Wait longer to ensure deletion completes
                                else:
                                    print(f"Browser {worker_id}: JavaScript approach did not complete deletion")
                                    
                            except Exception as e2:
                                print(f"Browser {worker_id}: Error with JavaScript delete: {e2}")
                            
                            # Fallback methods from before if delete doesn't work
                            if not deleted:
                                # Method 3: Look for "New chat" button
                                try:
                                    new_chat_buttons = driver.find_elements(By.XPATH, 
                                        '//a[contains(@href, "/chat") and contains(., "New chat")]')
                                    
                                    if new_chat_buttons:
                                        new_chat_buttons[0].click()
                                        print(f"Browser {worker_id}: Clicked 'New chat' button (fallback)")
                                        time.sleep(2)
                                        deleted = True
                                except Exception as e3:
                                    print(f"Browser {worker_id}: Error finding New chat button: {e3}")
                                
                                # Method 4: Navigate directly to a new chat as a final fallback
                                if not deleted:
                                    try:
                                        driver.get(self.config["chatgpt_url"] + "/chat")
                                        print(f"Browser {worker_id}: Navigated to new chat URL (final fallback)")
                                        time.sleep(3)
                                        deleted = True
                                    except Exception as e4:
                                        print(f"Browser {worker_id}: Error navigating to new chat: {e4}")
                                
                                        print(f"Browser {worker_id}: Error navigating to new chat: {e4}")
                                
                                if not deleted:
                                    print(f"Browser {worker_id}: Could not delete or clear chat, will try again on next processing")

                    except Exception as clear_err:
                        print(f"Browser {worker_id}: Error deleting chat: {clear_err}")
                        # Continue anyway, don't fail the processing
                print(f"\nCompleted batch {batch_idx//self.num_processes + 1}: {successful_count}/{batch_size} successful")
                
                # Wait briefly before starting next batch
                if batch_idx + self.num_processes < len(dirs):
                    print("Waiting 5 seconds before starting next batch...")
                    time.sleep(5)
        
        except Exception as e:
            print(f"Error during parallel processing: {e}")
            traceback.print_exc()
            
        finally:
            # Clean up all browsers
            for i, driver in enumerate(drivers):
                try:
                    driver.quit()
                    print(f"Browser {i+1} closed")
                except:
                    pass
            
            # Reset driver reference
            self.driver = None
        
        # Calculate overall time
        overall_end = time.time()
        total_time = overall_end - overall_start
        
        # Display summary
        print("\n=== Processing Summary ===")
        print(f"Total directories processed: {processed_count}")
        print(f"Successful: {successful_count}")
        print(f"Failed: {failed_count}")
        
        # Calculate and display statistics
        if successful_count > 0 and processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            hourly_rate = 3600 / avg_time * self.num_processes
            
            print(f"\nAverage processing time: {avg_time:.2f} seconds per image")
            print(f"Data collection rate: {hourly_rate:.2f} images per hour (with {self.num_processes} parallel processes)")
            print(f"Total time: {total_time:.2f} seconds")
            
            # Format as hours, minutes, seconds
            hours, remainder = divmod(total_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Total time: {int(hours)}h {int(minutes)}m {seconds:.2f}s")
        
        # Save statistics
        stats = self._save_parallel_stats(processed_count, successful_count, failed_count, processing_times, total_time)
        
        return successful_count > 0

    def _save_parallel_stats(self, processed, successful, failed, processing_times, total_time):
        """Save parallel processing statistics to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = f"emu_parallel_stats_{timestamp}.json"
        
        # Calculate statistics
        avg_time = 0
        hourly_rate = 0
        avg_time_per_batch = 0
        avg_time_per_image = 0
        
        if processing_times and len(processing_times) > 0:
            avg_time = sum(processing_times) / len(processing_times)
            hourly_rate = 3600 / avg_time * self.num_processes if avg_time > 0 else 0
            
            # Calculate batch statistics
            # Assuming each batch processes self.num_processes images in parallel
            batch_count = max(1, processed // self.num_processes)
            avg_time_per_batch = total_time / batch_count if batch_count > 0 else 0
            avg_time_per_image = avg_time_per_batch / self.num_processes if self.num_processes > 0 else 0
        
        # Format time as HH:MM:SS
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"
        
        # Create stats dictionary
        stats = {
            "timestamp": timestamp,
            "total_dirs_processed": processed,
            "successful": successful,
            "failed": failed,
            "total_time_seconds": total_time,
            "total_time_formatted": formatted_time,
            "avg_time_per_image_seconds": avg_time,
            "avg_time_per_batch_seconds": avg_time_per_batch,
            "avg_time_per_image_in_batch_seconds": avg_time_per_image,
            "images_per_hour": hourly_rate,
            "num_processes": self.num_processes,
            "num_processing_times_recorded": len(processing_times) if processing_times else 0
        }
        
        # Save to file
        try:
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"Statistics saved to {stats_file}")
            
            # Also print the new statistics
            if avg_time_per_batch > 0:
                print(f"Average time per batch: {avg_time_per_batch:.2f} seconds")
                print(f"Average time per image in batch: {avg_time_per_image:.2f} seconds")
        except Exception as e:
            print(f"Error saving statistics: {str(e)}")
            
        return stats

    def _setup_chrome_options(self, profile_dir):
        """Set up Chrome options with the specified profile directory."""
        import undetected_chromedriver as uc
        options = uc.ChromeOptions()
        
        # Configure user data directory
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Configure window size - use default values if not in config
        window_width = self.config.get("window_width", 1280)
        window_height = self.config.get("window_height", 800)
        options.add_argument(f"--window-size={window_width},{window_height}")
        
        # Add performance optimization flags
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        
        # Set debug level
        options.add_argument("--log-level=3")
        
        return options
    
    def _check_gpt_authentication(self, driver):
        """Check if authentication to ChatGPT is needed and wait for login"""
        import time
        
        # Check if we need to log in
        if "auth" in driver.current_url or "login" in driver.current_url:
            print("Authentication required. Please log in.")
            
            # Wait for login to complete (longer timeout)
            wait_time = self.config.get("login_wait_time", 180)
            print(f"Waiting up to {wait_time} seconds for login...")
            
            timeout = time.time() + wait_time
            while time.time() < timeout:
                try:
                    # Check if we've been redirected to the chat page
                    if "chat.openai.com" in driver.current_url and "auth" not in driver.current_url:
                        print("Successfully logged in")
                        break
                    time.sleep(1)
                except:
                    time.sleep(1)
            
            # If still on login page after timeout, raise exception
            if "auth" in driver.current_url or "login" in driver.current_url:
                raise Exception("Login timeout - authentication failed")
                
    def _worker_process(self, worker_id, dir_queue, result_queue, worker_profile, 
                      processed_counter, success_counter, failed_counter):
        """Worker process for parallel processing of directories"""
        import time
        import random
        import queue
        import multiprocessing.queues  # For proper queue type detection
        # Use the full import for undetected-chromedriver
        import undetected_chromedriver as uc
        from selenium.common.exceptions import NoSuchElementException, WebDriverException
        
        # Add small random delay to prevent race conditions
        time.sleep(random.uniform(0.5, 2.0))
        
        driver = None
        max_retries = 3
        
        try:
            # Initialize chrome with retries
            for attempt in range(max_retries):
                try:
                    print(f"Worker {worker_id}: Starting (attempt {attempt+1}/{max_retries})")
                    
                    # Setup Chrome options using the existing profile from manual login
                    options = self._setup_chrome_options(worker_profile)
                    
                    # Initialize driver
                    driver = uc.Chrome(options=options)
                    
                    # Navigate to ChatGPT
                    chatgpt_url = self.config.get("chatgpt_url", "https://chat.openai.com")
                    driver.get(chatgpt_url)
                    
                    # Wait for page to load
                    time.sleep(3)
                    
                    print(f"Worker {worker_id}: Browser initialized successfully")
                    break
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Calculate backoff time (1s, 3s, 9s, etc.)
                        backoff = (2 ** attempt) * 1.0 + random.uniform(0, 0.5)
                        print(f"Worker {worker_id}: Failed to initialize browser. Retrying in {backoff:.1f}s...")
                        print(f"Error: {str(e)}")
                        time.sleep(backoff)
                    else:
                        print(f"Worker {worker_id}: Failed to initialize browser after {max_retries} attempts")
                        print(f"Error: {str(e)}")
                        raise
            # Process directories from the queue
            local_processing_times = []
            
            while True:
                try:
                    # Get next directory from queue with timeout
                    directory = dir_queue.get(timeout=5)
                    
                    # Skip if output files already exist
                    output_jpg = os.path.join(directory, "output.jpg")
                    output_png = os.path.join(directory, "output.png")
                    
                    if (os.path.exists(output_jpg) and os.path.getsize(output_jpg) > 0) or \
                       (os.path.exists(output_png) and os.path.getsize(output_png) > 0):
                        print(f"Worker {worker_id}: Skipping {directory} (output already exists)")
                        
                        # Only call task_done if it's a multiprocessing.queues.Queue
                        if hasattr(dir_queue, 'task_done'):
                            dir_queue.task_done()
                            
                        with processed_counter.get_lock():
                            processed_counter.value += 1
                        with success_counter.get_lock():
                            success_counter.value += 1
                        continue
                    
                    print(f"Worker {worker_id}: Processing {directory}")
                    
                    # Process directory and track time
                    start_time = time.time()
                    
                    # Set the driver for this instance to use in process_directory
                    self.driver = driver
                    success = self.process_directory(directory)
                    self.driver = None  # Clear the reference
                    
                    end_time = time.time()
                    
                    # Update counters and processing time
                    processing_time = end_time - start_time
                    local_processing_times.append(processing_time)
                    
                    with processed_counter.get_lock():
                        processed_counter.value += 1
                        
                    if success:
                        with success_counter.get_lock():
                            success_counter.value += 1
                        result_queue.put({"processing_time": processing_time})
                        print(f"Worker {worker_id}: Successfully processed {directory} in {processing_time:.1f}s")
                    else:
                        with failed_counter.get_lock():
                            failed_counter.value += 1
                        print(f"Worker {worker_id}: Failed to process {directory}")
                    
                    # Mark task as done if the queue has this method
                    if hasattr(dir_queue, 'task_done'):
                        dir_queue.task_done()
                
                except queue.Empty:
                    # No more work
                    print(f"Worker {worker_id}: No more directories to process")
                    break
                    
                except Exception as e:
                    # Handle errors during processing
                    print(f"Worker {worker_id}: Error processing directory: {str(e)}")
                    
                    # Try to recover by refreshing the page
                    try:
                        print(f"Worker {worker_id}: Attempting to recover by refreshing the page")
                        driver.refresh()
                        time.sleep(5)  # Wait for page to load
                    except:
                        print(f"Worker {worker_id}: Failed to refresh page")
                    
                    # Mark task as done if the queue has this method
                    if 'directory' in locals() and hasattr(dir_queue, 'task_done'):
                        dir_queue.task_done()
                        
                    with failed_counter.get_lock():
                        failed_counter.value += 1
            
            # Report worker statistics
            result_queue.put({
                "worker_id": worker_id,
                "processing_times": local_processing_times
            })
            
        except Exception as e:
            # Handle worker-level errors
            print(f"Worker {worker_id}: Critical error: {str(e)}")
            
        finally:
            # Clean up
            if driver is not None:
                try:
                    driver.quit()
                except:
                    pass
                    
            print(f"Worker {worker_id}: Cleanup complete")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ChatGPT Automation for Emu Dataset using undetected-chromedriver")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--max_dirs", type=int, default=0, help="Maximum number of directories to process (per worker in parallel mode)")
    parser.add_argument("--profile", type=str, help="Path to Chrome profile directory")
    parser.add_argument("--use_coordinates", action="store_true", help="Use coordinate-based interaction instead of selectors")
    parser.add_argument("--calibrate", action="store_true", help="Run calibration mode to identify UI element coordinates")
    parser.add_argument("--parallel", action="store_true", help="Use parallel processing with multiple workers")
    parser.add_argument("--processes", type=int, default=8, help="Number of parallel processes to use")
    
    args = parser.parse_args()
    
    # Create processor
    processor = EmuGPTProcessor(args.config)
    
    # Override config with command line arguments
    if args.max_dirs > 0:
        processor.config["max_dirs_to_process"] = args.max_dirs
    if args.profile:
        processor.config["browser_profile"] = args.profile
        processor.user_profile = args.profile
    if args.use_coordinates:
        processor.config["use_coordinates"] = True
    if args.processes > 0:
        processor.num_processes = args.processes
    
    # Run processing (either parallel or single-threaded)
    if args.parallel:
        print(f"Running with parallel processing ({processor.num_processes} processes)")
        success = processor.run_parallel()
    else:
        print("Running with single-threaded processing")
        success = processor.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 