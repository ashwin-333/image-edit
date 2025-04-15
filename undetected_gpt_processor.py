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
        self.user_profile = "/Users/ashwin/chrome_chatgpt_profile_20250414_214423"
    
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
                    time.sleep(1)
                    
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
            
            # PRIORITY 2: Look for images from oaiusercontent.com domain (from screenshot)
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
            
            # PRIORITY 3: Look for images with class attributes matching the screenshot 
            print("Looking for images with class attributes from the screenshot...")
            try:
                class_images = self.driver.find_elements(By.CSS_SELECTOR, 'img.absolute.top-0, img.absolute.z-1, img.w-full')
                if class_images:
                    for img in class_images:
                        src = img.get_attribute('src')
                        if src and not ('avatar' in src.lower() or 'user' in src.lower()):
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                            time.sleep(1)
                            output_file = os.path.join(directory_path, "output.png")
                            img.screenshot(output_file)
                            print(f"Image saved to {output_file} (via class attributes)")
                            return True
            except Exception as e3:
                print(f"Error with class attributes approach: {str(e3)}")

            # PRIORITY 4: Try the aspect-ratio style approach from the screenshot
            print("Looking for images with aspect-ratio style...")
            try:
                images_with_style = self.driver.execute_script("""
                    const results = [];
                    const images = document.querySelectorAll('img');
                    
                    for (const img of images) {
                        const style = window.getComputedStyle(img);
                        if (style.aspectRatio === '0.666667 / 1' || 
                            style.aspectRatio === '0.6666666666666666 / 1' ||
                            img.style.aspectRatio === '0.666667 / 1' ||
                            img.getAttribute('style')?.includes('aspect-ratio: 0.666667 / 1')) {
                            results.push(img);
                        }
                    }
                    
                    return results;
                """)
                
                if images_with_style and len(images_with_style) > 0:
                    for img in images_with_style:
                        try:
                            src = img.get_attribute('src')
                            if src and src.startswith('http'):
                                import requests
                                output_file = os.path.join(directory_path, "output.png")
                                response = requests.get(src, stream=True)
                                if response.status_code == 200:
                                    with open(output_file, 'wb') as file:
                                        for chunk in response.iter_content(1024):
                                            file.write(chunk)
                                    print(f"Downloaded image with aspect-ratio style to {output_file}")
                                    return True
                            
                            # Fallback to screenshot
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                            time.sleep(1)
                            output_file = os.path.join(directory_path, "output.png")
                            img.screenshot(output_file)
                            print(f"Image saved to {output_file} (via aspect-ratio style)")
                            return True
                        except Exception:
                            continue
            except Exception as style_err:
                print(f"Error with aspect-ratio style approach: {style_err}")
                
            # PRIORITY 5: Last resort - use JavaScript to extract all image sources
            print("Using JavaScript to find any suitable images...")
            try:
                image_srcs = self.driver.execute_script("""
                    // Get all image URLs that look like they might be generated
                    const results = [];
                    const images = document.querySelectorAll('img');
                    
                    for (const img of images) {
                        const src = img.src || '';
                        const alt = img.alt || '';
                        const classes = img.className || '';
                        const style = img.getAttribute('style') || '';
                        
                        // Skip user avatars or small icons
                        if (alt.toLowerCase().includes('user') || 
                            src.toLowerCase().includes('avatar')) {
                            continue;
                        }
                        
                        // Skip very small images (likely icons)
                        if (img.width < 100 || img.height < 100) {
                            continue;
                        }
                        
                        // First check exact attributes from the screenshot
                        if (alt === 'Generated image' || 
                            src.includes('oaiusercontent.com') ||
                            style.includes('aspect-ratio: 0.666667 / 1') ||
                            classes.includes('absolute') ||
                            classes.includes('top-0') ||
                            classes.includes('z-1') ||
                            classes.includes('w-full')) {
                            
                            // Add image info to results with high priority (1)
                            results.push({
                                src: src,
                                width: img.width,
                                height: img.height,
                                alt: alt,
                                classes: classes,
                                priority: 1
                            });
                        }
                        // Then check more general patterns
                        else if (src.startsWith('blob:') ||
                                 src.startsWith('data:') || 
                                 src.includes('openai')) {
                            
                            // Add image info to results with medium priority (2)
                            results.push({
                                src: src,
                                width: img.width,
                                height: img.height,
                                alt: alt,
                                classes: classes,
                                priority: 2
                            });
                        }
                    }
                    
                    return results;
                """)
                
                if image_srcs and len(image_srcs) > 0:
                    # Sort by priority first, then by size
                    image_srcs.sort(key=lambda x: (x.get('priority', 99), -(x.get('width', 0) * x.get('height', 0))))
                    
                    for img_data in image_srcs:
                        src = img_data.get('src', '')
                        if src and src.startswith('http'):
                            try:
                                import requests
                                output_file = os.path.join(directory_path, "output.png")
                                response = requests.get(src, stream=True)
                                if response.status_code == 200:
                                    with open(output_file, 'wb') as file:
                                        for chunk in response.iter_content(1024):
                                            file.write(chunk)
                                    print(f"Downloaded image to {output_file} (via JavaScript extraction)")
                                    return True
                            except Exception as js_download_err:
                                print(f"Error downloading image from JavaScript: {js_download_err}")
            except Exception as js_err:
                print(f"Error with JavaScript image extraction: {js_err}")
            
            # If all automated attempts failed, create the output files
            print("Could not automatically identify and save any generated image")
            output_txt = os.path.join(directory_path, "output.txt")
            with open(output_txt, 'w') as f:
                f.write("Response captured - check for image")
            
            # Create blank output.png as placeholder
            try:
                from PIL import Image
                blank_img = Image.new('RGB', (512, 512), color='white')
                blank_img.save(os.path.join(directory_path, "output.png"))
                print("Created blank placeholder image")
            except:
                # In case PIL is not available, create empty file
                with open(os.path.join(directory_path, "output.png"), 'wb') as f:
                    f.write(b'')
                
            return False
            
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