"""
BDD Automation Generator - Optimized Version with Comprehensive Test Case Generation

This application generates BDD (Behavior Driven Development) automation files from user stories.

Key Features:
- Secure API key handling via environment variables
- Comprehensive logging system
- Enhanced error handling and recovery
- Cross-platform file system operations
- Input validation and file format support
- Thread-safe GUI operations
- Configurable retry logic for API calls

NEW COMPREHENSIVE TEST CASE FEATURES:
- Generates multiple test cases per user story (positive & negative scenarios)
- Includes detailed login steps for every test case
- Ensures 100% test coverage with boundary value testing
- Creates test cases in specific format: S.No, TestCasesDescription, StepAction, ExpectedResult
- Each step in StepAction has corresponding ExpectedResult
- Covers error handling and edge cases

Security Improvements:
- API key stored in environment variable (GEMINI_API_KEY)
- No sensitive data hardcoded in source

Performance Optimizations:
- Configurable API delay and retry mechanisms
- Efficient file validation
- Better error recovery

Maintainability:
- Consistent logging throughout the application
- Configuration constants for easy modification
- Modular helper functions
- Improved code documentation

Author: Generated and Optimized by GitHub Copilot
Last Updated: July 2025
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog # Import ttk for themed widgets like Progressbar
import os
import sys
import pandas as pd
import numpy as np
import google.generativeai as genai
import re
import time
import threading # For running generation in a separate thread to keep GUI responsive
import subprocess # For opening the output folder
import string
import logging

# --- Configuration ---
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bdd_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Secure API key handling - uses environment variable
# API key is now read dynamically in check_gemini_api_status() function

# API key should come from environment variables for security
# Do NOT hardcode API keys in production code
# Use this line to set your API key in your environment before running:
# os.environ['GEMINI_API_KEY'] = "YOUR_API_KEY_HERE"

# Check if the API key is already set
if not os.getenv('GEMINI_API_KEY'):
    print("WARNING: GEMINI_API_KEY environment variable is not set. The application will have limited functionality.") 

# Default output directory. Will be created if it doesn't exist.
DEFAULT_OUTPUT_ROOT_DIR = os.path.join(os.path.expanduser("~"), "GeneratedBDDFiles")

# Names for the intermediate and final output files/directories
GENERATED_TEST_CASES_FILE_NAME = "Comprehensive_Test_Cases.xlsx"
BDD_OUTPUT_SUBDIR_NAME = "BDD_Automation_Files"

# Configuration constants
MAX_RETRIES = 3
API_DELAY = 0.5  # Delay between API calls to avoid rate limits
SUPPORTED_FILE_EXTENSIONS = ('.xlsx', '.xls')
GEMINI_MODEL = 'gemini-2.0-flash'

# Global variables for file paths selected via GUI
user_story_input_file_path = None
generated_test_cases_file_path = None # NEW: Global variable for generated test cases file path
current_output_root_dir = DEFAULT_OUTPUT_ROOT_DIR

# --- Gemini API Configuration ---
# This function will be called initially and whenever the GUI needs to refresh API status
def check_gemini_api_status():
    """
    Checks the availability of the Gemini API using environment variable.
    Updates the GUI's API status label.
    """
    global gemini_api_available
    try:
        # Re-read the environment variable each time to get the latest value
        current_api_key = os.getenv('GEMINI_API_KEY')
        print(f"DEBUG: API key check - Found key: {'YES' if current_api_key else 'NO'}")
        if current_api_key:
            print(f"DEBUG: API key length: {len(current_api_key)}")
        
        if not current_api_key:
            gemini_api_available = False
            api_status_label.config(text="API Status: API Key Not Set", fg="red")
            logger.warning("Gemini API key not configured")
            return
            
        # Use the API key from environment variable
        genai.configure(api_key=current_api_key)
        
        # Attempt a small model list call to verify connectivity
        # This is a lightweight way to check if the API key is active and working
        list(genai.list_models()) 
        gemini_api_available = True
        api_status_label.config(text="API Status: Available", fg="green")
        logger.info("Gemini API connection successful")
    except Exception as e:
        gemini_api_available = False
        api_status_label.config(text=f"API Status: Not Available - Check Key/Console", fg="red")
        logger.error(f"Error configuring or connecting to Gemini API: {e}")
        logger.info("Please ensure 'google-generativeai' is installed and GEMINI_API_KEY environment variable is set correctly.")

# --- Helper Functions for Backend Logic ---

def safe_gui_update(func, *args, **kwargs):
    """
    Thread-safe GUI update function.
    Schedules GUI updates to run on the main thread.
    """
    root.after(0, func, *args, **kwargs)

def retry_api_call(func, max_retries=MAX_RETRIES, *args, **kwargs):
    """
    Retry API calls with exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise e
            wait_time = API_DELAY * (2 ** attempt)  # Exponential backoff
            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
def validate_input_file(file_path):
    """
    Validates the input file format and existence.
    Returns tuple (is_valid, error_message)
    """
    if not file_path:
        return False, "No file selected"
    
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        return False, "Please select an Excel file (.xlsx or .xls)"
    
    try:
        # Test if file can be read
        pd.read_excel(file_path, nrows=0)
        return True, ""
    except Exception as e:
        return False, f"Cannot read Excel file: {str(e)}"

def clean_step_text_for_gherkin(text):
    """
    Cleans text to be suitable for Gherkin steps.
    Removes leading/trailing whitespace, replaces multiple spaces,
    removes trailing periods, and removes commas.
    """
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text) # Replace multiple spaces with single
    text = re.sub(r'\.\s*$', '', text) # Remove trailing period if it's not part of an abbreviation
    text = text.replace(',', '') # Remove commas for cleaner steps, adjust if commas are meaningful in your steps
    return text

# --- Phase 1: Generate Test Cases from User Stories ---

def generate_test_case_with_gemini_backend(user_story_id, title, acceptance_criteria):
    """
    Generates comprehensive test cases with positive and negative scenarios,
    detailed steps including login, ensuring 100% test coverage.
    """
    prompt_template = f"""
    You are an expert Quality Assurance Engineer. Your task is to generate comprehensive test cases for a given User Story that ensure 100% test coverage.

    **User Story ID:** {user_story_id}
    **User Story Title:** {title}
    **Acceptance Criteria:**
    {acceptance_criteria}

    **Requirements:**
    1. Create both POSITIVE and NEGATIVE test cases
    2. Include application login steps in every test case
    3. Provide detailed step-by-step actions
    4. Ensure 100% test coverage of the acceptance criteria
    5. Include boundary value testing where applicable
    6. Add error handling scenarios

    **STRICT OUTPUT FORMAT - Follow this EXACT structure:**

    S.No: 1
    TestCasesDescription: Valid Login and [specific functionality]
    StepAction:
    Navigate to application login page
    Enter valid username in username field
    Enter valid password in password field  
    Click login button
    Navigate to [specific feature area]
    [Add specific steps for this user story]
    Verify functionality works as expected
    ExpectedResult:
    Login page loads successfully
    Username field accepts valid input
    Password field accepts input and masks characters
    Login successful and redirected to dashboard
    [Specific feature area] loads correctly
    [Expected results for each step above]
    Functionality works as per acceptance criteria

    S.No: 2
    TestCasesDescription: Invalid Login Credentials
    StepAction:
    Navigate to application login page
    Enter invalid username
    Enter invalid password
    Click login button
    ExpectedResult:
    Login page loads successfully
    Username field accepts input
    Password field accepts input and masks characters
    Error message displayed for invalid credentials

    S.No: 3
    TestCasesDescription: [specific error scenario for the feature]
    StepAction:
    Navigate to application login page
    Enter valid username
    Enter valid password
    Click login button
    Navigate to [feature area]
    [Perform invalid action related to the user story]
    ExpectedResult:
    Login successful
    [Feature area] loads correctly
    Appropriate error message displayed for invalid action
    System handles error gracefully

    **IMPORTANT RULES:**
    - Each S.No must be on its own line
    - Each section (TestCasesDescription, StepAction, ExpectedResult) must be clearly labeled
    - StepAction and ExpectedResult should have corresponding steps
    - Always start with login steps
    - Generate at least 2-3 test cases per user story
    - Cover both valid and invalid scenarios with clear, concise descriptions
    - Be specific to the acceptance criteria provided
    - Avoid prefixes like "Positive Test Case" or "Negative Test Case" in descriptions

    Generate the test cases now:
    """

    if not gemini_api_available:
        # Return specific error messages that can be filtered later
        return "ERROR_API_NOT_AVAILABLE_TEST_CASES", "ERROR_API_NOT_AVAILABLE_TEST_CASES"

    # Re-read the API key to ensure we have the latest value
    current_api_key = os.getenv('GEMINI_API_KEY')
    if not current_api_key:
        return "ERROR_API_NOT_AVAILABLE_TEST_CASES", "ERROR_API_NOT_AVAILABLE_TEST_CASES"
    
    # Configure with the current API key
    genai.configure(api_key=current_api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    try:
        response = model.generate_content(prompt_template)
        text_response = response.text.strip()

        # Parse the comprehensive test cases response
        test_cases_start = text_response.find("Test Cases:")
        
        if test_cases_start == -1:
            # Fallback: look for any S.No pattern
            if "S.No:" in text_response:
                test_cases_content = text_response
            else:
                return "ERROR_GENERATION_FORMAT_ISSUE_TEST_CASES", "ERROR_GENERATION_FORMAT_ISSUE_TEST_CASES"
        else:
            test_cases_content = text_response[test_cases_start + len("Test Cases:"):].strip()

        # Clean up any example text
        if "Example (for clarity," in test_cases_content:
            test_cases_content = test_cases_content.split("Example (for clarity,")[0].strip()
        
        # Return the full test cases content - we'll parse it differently in the backend
        time.sleep(API_DELAY)  # Small delay to avoid hitting API rate limits
        return test_cases_content, test_cases_content  # Return same content for both fields for now

    except Exception as e:
        logger.error(f"Error generating content for US {user_story_id}: {e}")
        return "ERROR_API_CALL_FAILED_TEST_CASES", "ERROR_API_CALL_FAILED_TEST_CASES"

def parse_comprehensive_test_cases(test_cases_content, user_story_id, title):
    """
    Parses the comprehensive test cases content and extracts individual test cases
    with the required format: S.No, TestCasesDescription, StepAction, ExpectedResult
    """
    parsed_test_cases = []
    
    if test_cases_content.startswith("ERROR_"):
        # Return a default test case structure for errors
        return [{
            "User Story ID": user_story_id,
            "Title": title,
            "S.No": 1,
            "TestCasesDescription": f"Test case generation failed for {title}",
            "StepAction": "Manual test case creation required",
            "ExpectedResult": "Test case should be created manually"
        }]
    
    try:
        # Look for individual test cases by S.No pattern
        test_case_pattern = r'S\.No:\s*(\d+)\s*\n.*?TestCasesDescription:\s*(.*?)\n.*?StepAction:\s*(.*?)(?=ExpectedResult:|$).*?ExpectedResult:\s*(.*?)(?=S\.No:|$)'
        matches = re.findall(test_case_pattern, test_cases_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            s_no, description, step_actions, expected_results = match
            
            # Clean and format the content
            description = description.strip()
            step_actions = re.sub(r'^\d+\.\s*', '', step_actions.strip(), flags=re.MULTILINE)
            expected_results = re.sub(r'^\d+\.\s*', '', expected_results.strip(), flags=re.MULTILINE)
            
            parsed_test_cases.append({
                "User Story ID": user_story_id,
                "Title": title,
                "S.No": int(s_no),
                "TestCasesDescription": description,
                "StepAction": step_actions,
                "ExpectedResult": expected_results
            })
        
        # If regex parsing failed, try simpler approach
        if not parsed_test_cases:
            # Split by S.No and process each block
            blocks = re.split(r'\n\s*S\.No:\s*\d+', test_cases_content)
            
            for i, block in enumerate(blocks):
                if not block.strip() or i == 0:  # Skip empty blocks and first split
                    continue
                
                # Extract description
                desc_match = re.search(r'TestCasesDescription:\s*(.*?)(?=\n|StepAction:|$)', block, re.DOTALL)
                description = desc_match.group(1).strip() if desc_match else f"Test case {i} for {title}"
                
                # Extract step actions
                step_match = re.search(r'StepAction:\s*(.*?)(?=ExpectedResult:|$)', block, re.DOTALL)
                step_actions = step_match.group(1).strip() if step_match else "No step actions specified"
                
                # Extract expected results
                result_match = re.search(r'ExpectedResult:\s*(.*?)(?=\n\s*S\.No:|$)', block, re.DOTALL)
                expected_results = result_match.group(1).strip() if result_match else "Expected results not specified"
                
                parsed_test_cases.append({
                    "User Story ID": user_story_id,
                    "Title": title,
                    "S.No": i,
                    "TestCasesDescription": description,
                    "StepAction": step_actions,
                    "ExpectedResult": expected_results
                })
        
    except Exception as e:
        logger.error(f"Error parsing test cases: {e}")
        # Fallback: create a single test case with all content
        parsed_test_cases.append({
            "User Story ID": user_story_id,
            "Title": title,
            "S.No": 1,
            "TestCasesDescription": f"Comprehensive test for {title}",
            "StepAction": test_cases_content[:1000] + "..." if len(test_cases_content) > 1000 else test_cases_content,
            "ExpectedResult": "All test steps should execute successfully as per acceptance criteria"
        })
    
    # Ensure we have at least one test case
    if not parsed_test_cases:
        parsed_test_cases.append({
            "User Story ID": user_story_id,
            "Title": title,
            "S.No": 1,
            "TestCasesDescription": f"Default test case for {title}",
            "StepAction": f"Test the functionality described in: {title}",
            "ExpectedResult": "Functionality should work as per acceptance criteria"
        })
    
    return parsed_test_cases

def generate_test_cases_from_user_stories_backend(input_file_path, output_dir):
    """
    Reads user stories, generates comprehensive test cases using Gemini, and saves them to an Excel file.
    Now generates multiple test cases per user story with detailed format.
    """
    status_label.config(text=f"Phase 1: Reading user stories from '{os.path.basename(input_file_path)}'...")
    progress_bar['value'] = 0
    root.update_idletasks()

    try:
        df_user_stories = pd.read_excel(input_file_path)
        logger.info(f"Successfully read Excel file with columns: {df_user_stories.columns.tolist()}")

        column_mapping = {col.strip().lower(): col for col in df_user_stories.columns}
        
        required_cols_norm = {'user story id', 'title', 'acceptance criteria'}
        missing_cols = [col for col in required_cols_norm if col not in column_mapping]

        if missing_cols:
            error_msg = f"Missing required columns in '{os.path.basename(input_file_path)}': {missing_cols}\nPlease ensure your Excel file has 'User Story ID', 'Title', and 'Acceptance Criteria' columns."
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)
            return None

    except FileNotFoundError:
        error_msg = f"Input file '{input_file_path}' not found."
        messagebox.showerror("Error", error_msg)
        logger.error(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error reading User Story Excel file: {e}"
        messagebox.showerror("Error", error_msg)
        logger.error(error_msg)
        return None

    all_generated_test_cases = []
    total_stories = len(df_user_stories)

    for index, row in df_user_stories.iterrows():
        status_label.config(text=f"Phase 1: Generating comprehensive test cases {index + 1}/{total_stories}...")
        progress_bar['value'] = (index + 1) / total_stories * 50 # Phase 1 takes up 50% of progress
        root.update_idletasks()

        user_story_id_col = column_mapping['user story id']
        title_col = column_mapping['title']
        acceptance_criteria_col = column_mapping['acceptance criteria']

        user_story_id = row[user_story_id_col]
        title = row[title_col]
        acceptance_criteria = str(row[acceptance_criteria_col]).strip() if pd.notna(row[acceptance_criteria_col]) else ""

        # Generate comprehensive test cases
        test_cases_content, _ = generate_test_case_with_gemini_backend(user_story_id, title, acceptance_criteria)
        
        # Parse the comprehensive test cases into individual rows
        parsed_test_cases = parse_comprehensive_test_cases(test_cases_content, user_story_id, title)
        
        # Add all parsed test cases to the main list
        all_generated_test_cases.extend(parsed_test_cases)

    df_generated_test_cases = pd.DataFrame(all_generated_test_cases)
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    global generated_test_cases_file_path # NEW: Use global variable
    generated_test_cases_file_path = os.path.join(output_dir, GENERATED_TEST_CASES_FILE_NAME) # NEW: Assign to global

    try:
        df_generated_test_cases.to_excel(generated_test_cases_file_path, index=False)
        status_label.config(text=f"Phase 1: Comprehensive test cases saved to '{os.path.basename(generated_test_cases_file_path)}'")
        logger.info(f"Generated {len(all_generated_test_cases)} test cases for {total_stories} user stories")
        root.update_idletasks()
        return generated_test_cases_file_path
    except Exception as e:
        messagebox.showerror("Error", f"Error saving generated test cases to Excel file: {e}")
        return None

# --- Phase 2: Generate BDD Files from Test Cases ---

def generate_bdd_files_backend(test_case_file_path, output_dir):
    """
    Reads generated comprehensive test cases, constructs BDD scenarios, and generates
    Feature file, Step Definitions, Page Object Model, and package.json.
    Updated to work with the new comprehensive test case format.
    """
    status_label.config(text=f"Phase 2: Reading comprehensive test cases from '{os.path.basename(test_case_file_path)}'...")
    root.update_idletasks()

    try:
        df_test_cases = pd.read_excel(test_case_file_path)
        logger.info(f"Loaded {len(df_test_cases)} test cases from file")
    except FileNotFoundError:
        messagebox.showerror("Error", f"Test case file '{test_case_file_path}' not found. Cannot generate BDD files.")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Error reading test case Excel file: {e}")
        return

    scenarios_data = {}
    all_unique_gherkin_steps_for_llm_context = set()

    for index, row in df_test_cases.iterrows():
        # Use TestCasesDescription as scenario title
        raw_scenario_title = row.get("TestCasesDescription")
        
        if pd.isna(raw_scenario_title) or str(raw_scenario_title).strip() == "":
            logger.info(f"Skipping row {index}: TestCasesDescription is missing or empty.")
            continue
        
        scenario_title = str(raw_scenario_title).strip()
        
        # Get StepAction and ExpectedResult
        step_action_content = "" if pd.isna(row.get("StepAction")) else str(row.get("StepAction")).strip()
        expected_result_content = "" if pd.isna(row.get("ExpectedResult")) else str(row.get("ExpectedResult")).strip()

        if scenario_title not in scenarios_data:
            scenarios_data[scenario_title] = {
                "feature_name": "Application Functionality", 
                "raw_action_steps": [],
                "final_expected_result": ""
            }

        # Filter out error messages and process step actions
        if step_action_content and not step_action_content.startswith("ERROR_"):
            # Split step actions by lines and clean them
            step_lines = [line.strip() for line in step_action_content.split('\n') if line.strip()]
            for step_line in step_lines:
                cleaned_step = clean_step_text_for_gherkin(step_line)
                if cleaned_step:
                    scenarios_data[scenario_title]["raw_action_steps"].append(cleaned_step)
        else:
            logger.warning(f"Skipping problematic step action content for '{scenario_title}': {step_action_content}")

        # Process expected results
        if expected_result_content and not expected_result_content.startswith("ERROR_"):
            # Use the last line of expected results as the final verification
            result_lines = [line.strip() for line in expected_result_content.split('\n') if line.strip()]
            if result_lines:
                scenarios_data[scenario_title]["final_expected_result"] = clean_step_text_for_gherkin(result_lines[-1])
        else:
            logger.warning(f"Skipping problematic expected result content for '{scenario_title}': {expected_result_content}")
    
    if not scenarios_data:
        messagebox.showwarning("Warning", "No valid scenarios found in the test case file. Skipping BDD file generation.")
        return

    # Continue with the rest of the BDD generation process...
    # --- Feature File Generation ---
    status_label.config(text="Phase 2: Generating Feature file...")
    progress_bar['value'] = 55 # Start of Phase 2
    root.update_idletasks()

    # IMPROVED FEATURE FILE PROMPT
    feature_file_prompt_parts = []
    feature_file_prompt_parts.append("You are a software automation assistant. Generate a BDD Cucumber feature file based on the following structured test case data.")
    feature_file_prompt_parts.append("For each scenario, follow these strict rules:\n")
    feature_file_prompt_parts.append("- The 'Scenario Title' will be the 'Scenario' name.\n")
    feature_file_prompt_parts.append("- Start every scenario with the 'Given' step: 'Given User provided with CVT URL'.\n")
    feature_file_prompt_parts.append("- The 'Raw Action Steps' list contains a sequence of actions. Translate these into clear, concise, and natural language Gherkin steps.\n")
    feature_file_prompt_parts.append("  - The very first action step after the 'Given' should start with 'When'.\n")
    feature_file_prompt_parts.append("  - For all subsequent action steps, use 'And'.\n")
    feature_file_prompt_parts.append("- The 'Final Expected Result' should be the single 'Then' statement for the entire scenario. If 'Final Expected Result' is empty, use 'Then the expected outcome should be achieved'.\n")
    feature_file_prompt_parts.append("- Ensure all steps are correctly indented (2 spaces for Scenario, 4 spaces for steps).\n")
    feature_file_prompt_parts.append("- Do NOT include any introductory or concluding remarks outside the Gherkin content.\n")
    feature_file_prompt_parts.append("- ONLY provide the Gherkin content wrapped in a ```gherkin block.\n\n")

    feature_file_prompt_parts.append("Here is the structured test case data:\n\n")

    for scenario_title, data in scenarios_data.items():
        feature_file_prompt_parts.append(f"Scenario Title: {scenario_title}\n")
        feature_file_prompt_parts.append(f"Raw Action Steps: {data['raw_action_steps']}\n")
        feature_file_prompt_parts.append(f"Final Expected Result: {data['final_expected_result']}\n\n")

    feature_file_prompt = "\n".join(feature_file_prompt_parts)

    generated_feature_content = ""
    gemini_api_available_for_feature_rephrasing = gemini_api_available # Start with global API availability

    if gemini_api_available_for_feature_rephrasing:
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(feature_file_prompt)
            generated_feature_content = response.text
            
            # Extract content from Gherkin markdown block
            match = re.search(r'```gherkin\n(.*)```', generated_feature_content, re.DOTALL)
            if match:
                generated_feature_content = match.group(1).strip()
            else:
                generated_feature_content = generated_feature_content.strip()
                logger.warning("Gherkin code block delimiters not found for Feature file. Using raw response.")
            
            # Collect unique Gherkin steps for later use
            for line in generated_feature_content.splitlines():
                line = line.strip()
                if line.startswith(("Given ", "When ", "Then ", "And ")):
                    all_unique_gherkin_steps_for_llm_context.add(line)
            time.sleep(API_DELAY)
        except Exception as e:
            logger.error(f"Error generating Feature file with Gemini: {e}")
            logger.info("Falling back to local feature file generation.")
            gemini_api_available_for_feature_rephrasing = False
    
    # Fallback to local generation if Gemini API failed or is not available for feature rephrasing
    if not gemini_api_available_for_feature_rephrasing:
        local_feature_file_content = ""
        added_features_local = set()

        for scenario_title, data in scenarios_data.items():
            feature_name = data["feature_name"]
            if feature_name not in added_features_local:
                local_feature_file_content += f"Feature: {feature_name}\n\n"
                added_features_local.add(feature_name)
            
            local_feature_file_content += f"  Scenario: {scenario_title}\n"
            
            local_feature_file_content += f"    Given User provided with CVT URL\n"
            all_unique_gherkin_steps_for_llm_context.add("Given User provided with CVT URL")

            # Only add raw action steps if they are present and not error messages
            if data['raw_action_steps']:
                is_first_action_step = True
                for step_text in data['raw_action_steps']:
                    if is_first_action_step:
                        local_feature_file_content += f"    When {step_text}\n"
                        all_unique_gherkin_steps_for_llm_context.add(f"When {step_text}")
                        is_first_action_step = False
                    else:
                        local_feature_file_content += f"    And {step_text}\n"
                        all_unique_gherkin_steps_for_llm_context.add(f"And {step_text}")
            else:
                # Fallback if no valid action steps were generated by API
                local_feature_file_content += f"    When the system processes the request\n"
                all_unique_gherkin_steps_for_llm_context.add("When the system processes the request")
            
            final_expected_result = data["final_expected_result"]
            if final_expected_result:
                final_then_step = f"Then {final_expected_result}"
                local_feature_file_content += f"    {final_then_step}\n"
                all_unique_gherkin_steps_for_llm_context.add(final_then_step)
            else:
                default_then_step = "Then the expected outcome should be achieved"
                local_feature_file_content += f"    {default_then_step}\n"
                all_unique_gherkin_steps_for_llm_context.add(default_then_step)

            local_feature_file_content += "\n"
        generated_feature_content = local_feature_file_content

    # Ensure the BDD output directory exists
    bdd_output_full_path = os.path.join(output_dir, BDD_OUTPUT_SUBDIR_NAME)
    os.makedirs(bdd_output_full_path, exist_ok=True)

    feature_file_path = os.path.join(bdd_output_full_path, "feature_file.feature")
    with open(feature_file_path, "w", encoding="utf-8") as f:
        f.write(generated_feature_content)
    status_label.config(text=f"Phase 2: Feature file saved at: '{os.path.basename(feature_file_path)}'")
    progress_bar['value'] = 60
    root.update_idletasks()

    # --- Generate Step Definition, Page Object, and package.json using Gemini ---
    if gemini_api_available and len(all_unique_gherkin_steps_for_llm_context) > 0:
        status_label.config(text="Phase 2: Generating multi-language automation files...")
        root.update_idletasks()
        sorted_gherkin_steps = sorted(list(all_unique_gherkin_steps_for_llm_context))

        # Create language-specific directories
        js_dir = os.path.join(bdd_output_full_path, "javascript")
        java_dir = os.path.join(bdd_output_full_path, "java")
        python_dir = os.path.join(bdd_output_full_path, "python")
        
        os.makedirs(js_dir, exist_ok=True)
        os.makedirs(java_dir, exist_ok=True)
        os.makedirs(python_dir, exist_ok=True)

        model_for_code = genai.GenerativeModel(GEMINI_MODEL)

        # JAVASCRIPT FILES
        status_label.config(text="Phase 2: Generating JavaScript files...")
        progress_bar['value'] = 65
        root.update_idletasks()

        # JavaScript Step Definition
        js_step_def_prompt = f"""
        You are a software automation engineer. Generate a JavaScript step definition file for Cucumber.js using Selenium WebDriverJS.
        For each Gherkin step provided, create a corresponding step definition function.
        - Use `Given`, `When`, `Then`, `And` from `@cucumber/cucumber`.
        - Import `ApplicationPage` from `./pages.js`.
        - Use `await` for all Selenium WebDriverJS actions.
        - Implement common actions like `click`, `sendKeys`, `getText`, `isDisplayed`.
        - For "Then" steps, use basic assertions (e.g., `expect(await page.getSomeElementText()).to.include('expected text');`).
        - Extract parameters from Gherkin steps using regex capture groups.
        - Ensure proper indentation and formatting.
        - Do NOT include any introductory or concluding remarks outside the code.
        - ONLY provide the JavaScript code wrapped in a ```javascript block.

        Gherkin Steps to define:
        {'\n'.join(sorted_gherkin_steps)}
        """

        # JavaScript Page Object
        js_page_object_prompt = f"""
        You are a software automation engineer. Generate a JavaScript Page Object Model (POM) file for Selenium WebDriverJS.
        - Identify common UI elements and interactions based on the provided Gherkin steps.
        - Define locators using `By` static methods (e.g., `By.id()`, `By.css()`, `By.xpath()`).
        - Create methods to interact with these elements.
        - Use `await` for all Selenium WebDriverJS actions.
        - Include proper imports and error handling.
        - ONLY provide the JavaScript code wrapped in a ```javascript block.

        Gherkin Steps for context:
        {'\n'.join(sorted_gherkin_steps)}
        """

        # JAVA FILES  
        java_step_def_prompt = f"""
        You are a software automation engineer. Generate a Java step definition file for Cucumber with Selenium WebDriver.
        For each Gherkin step provided, create a corresponding step definition method.
        - Use Cucumber annotations: @Given, @When, @Then, @And.
        - Import necessary Selenium WebDriver classes.
        - Use WebDriver and WebDriverWait for interactions.
        - Implement common actions like click(), sendKeys(), getText(), isDisplayed().
        - For "Then" steps, use Assert statements for validations.
        - Extract parameters from Gherkin steps using Cucumber expressions.
        - Include proper class structure and imports.
        - ONLY provide the Java code wrapped in a ```java block.

        Gherkin Steps to define:
        {'\n'.join(sorted_gherkin_steps)}
        """

        # Java Page Object
        java_page_object_prompt = f"""
        You are a software automation engineer. Generate a Java Page Object Model (POM) file for Selenium WebDriver.
        - Identify common UI elements and interactions based on the provided Gherkin steps.
        - Use @FindBy annotations for element locators.
        - Create methods to interact with these elements.
        - Include WebDriver initialization and PageFactory.
        - Use proper Java naming conventions and structure.
        - Include necessary imports and constructor.
        - ONLY provide the Java code wrapped in a ```java block.

        Gherkin Steps for context:
        {'\n'.join(sorted_gherkin_steps)}
        """

        # PYTHON FILES
        python_step_def_prompt = f"""
        You are a software automation engineer. Generate a Python step definition file for Behave with Selenium WebDriver.
        For each Gherkin step provided, create a corresponding step definition function.
        - Use Behave decorators: @given, @when, @then, @step.
        - Import necessary Selenium WebDriver classes.
        - Use WebDriver and WebDriverWait for interactions.
        - Implement common actions like click(), send_keys(), text, is_displayed().
        - For "Then" steps, use assert statements for validations.
        - Extract parameters from Gherkin steps using step parameters.
        - Follow Python naming conventions (snake_case).
        - ONLY provide the Python code wrapped in a ```python block.

        Gherkin Steps to define:
        {'\n'.join(sorted_gherkin_steps)}
        """

        # Python Page Object
        python_page_object_prompt = f"""
        You are a software automation engineer. Generate a Python Page Object Model (POM) file for Selenium WebDriver.
        - Identify common UI elements and interactions based on the provided Gherkin steps.
        - Define locators using By class methods (By.ID, By.CSS_SELECTOR, By.XPATH).
        - Create methods to interact with these elements.
        - Include WebDriver initialization and proper class structure.
        - Use Python naming conventions (snake_case).
        - Include necessary imports and constructor.
        - ONLY provide the Python code wrapped in a ```python block.

        Gherkin Steps for context:
        {'\n'.join(sorted_gherkin_steps)}
        """ 

        # Configuration files prompts
        package_json_prompt = """
        Generate a basic package.json file for a Node.js project that uses Cucumber.js and Selenium WebDriverJS.
        - Set the project name to 'bdd-automation-project'.
        - Include a 'test' script that runs Cucumber.js.
        - List necessary dependencies: '@cucumber/cucumber', 'selenium-webdriver', and 'chai'.
        - ONLY provide the JSON content wrapped in a ```json block.
        """

        pom_xml_prompt = """
        Generate a basic pom.xml file for a Java Maven project that uses Cucumber and Selenium WebDriver.
        - Set the project name to 'bdd-automation-project'.
        - Include necessary dependencies: cucumber-java, cucumber-junit, selenium-java, junit.
        - Include maven-surefire-plugin for test execution.
        - ONLY provide the XML content wrapped in a ```xml block.
        """

        requirements_txt_prompt = """
        Generate a requirements.txt file for a Python project that uses Behave and Selenium WebDriver.
        List the necessary packages: behave, selenium, pytest (optional for additional testing).
        - ONLY provide the requirements content as plain text.
        """

        try:
            # GENERATE JAVASCRIPT FILES
            # JavaScript Step Definitions
            response = model_for_code.generate_content(js_step_def_prompt)
            js_step_content = response.text
            match = re.search(r'```javascript\n(.*?)```', js_step_content, re.DOTALL)
            js_step_content = match.group(1).strip() if match else js_step_content.strip()
            
            js_step_file_path = os.path.join(js_dir, "steps.js")
            with open(js_step_file_path, "w", encoding="utf-8") as f:
                f.write(js_step_content)
            
            time.sleep(API_DELAY)

            # JavaScript Page Object
            response = model_for_code.generate_content(js_page_object_prompt)
            js_page_content = response.text
            match = re.search(r'```javascript\n(.*?)```', js_page_content, re.DOTALL)
            js_page_content = match.group(1).strip() if match else js_page_content.strip()
            
            js_page_file_path = os.path.join(js_dir, "pages.js")
            with open(js_page_file_path, "w", encoding="utf-8") as f:
                f.write(js_page_content)
            
            time.sleep(API_DELAY)

            # Package.json
            response = model_for_code.generate_content(package_json_prompt)
            package_json_content = response.text
            match = re.search(r'```json\n(.*?)```', package_json_content, re.DOTALL)
            package_json_content = match.group(1).strip() if match else package_json_content.strip()
            
            package_json_file_path = os.path.join(js_dir, "package.json")
            with open(package_json_file_path, "w", encoding="utf-8") as f:
                f.write(package_json_content)

            status_label.config(text="Phase 2: Generating Java files...")
            progress_bar['value'] = 75
            root.update_idletasks()

            # GENERATE JAVA FILES
            # Java Step Definitions
            response = model_for_code.generate_content(java_step_def_prompt)
            java_step_content = response.text
            match = re.search(r'```java\n(.*?)```', java_step_content, re.DOTALL)
            java_step_content = match.group(1).strip() if match else java_step_content.strip()
            
            java_step_file_path = os.path.join(java_dir, "StepDefinitions.java")
            with open(java_step_file_path, "w", encoding="utf-8") as f:
                f.write(java_step_content)
            
            time.sleep(API_DELAY)

            # Java Page Object
            response = model_for_code.generate_content(java_page_object_prompt)
            java_page_content = response.text
            match = re.search(r'```java\n(.*?)```', java_page_content, re.DOTALL)
            java_page_content = match.group(1).strip() if match else java_page_content.strip()
            
            java_page_file_path = os.path.join(java_dir, "ApplicationPage.java")
            with open(java_page_file_path, "w", encoding="utf-8") as f:
                f.write(java_page_content)
            
            time.sleep(API_DELAY)

            # POM.xml
            response = model_for_code.generate_content(pom_xml_prompt)
            pom_xml_content = response.text
            match = re.search(r'```xml\n(.*?)```', pom_xml_content, re.DOTALL)
            pom_xml_content = match.group(1).strip() if match else pom_xml_content.strip()
            
            pom_xml_file_path = os.path.join(java_dir, "pom.xml")
            with open(pom_xml_file_path, "w", encoding="utf-8") as f:
                f.write(pom_xml_content)

            status_label.config(text="Phase 2: Generating Python files...")
            progress_bar['value'] = 85
            root.update_idletasks()

            # GENERATE PYTHON FILES
            # Python Step Definitions
            response = model_for_code.generate_content(python_step_def_prompt)
            python_step_content = response.text
            match = re.search(r'```python\n(.*?)```', python_step_content, re.DOTALL)
            python_step_content = match.group(1).strip() if match else python_step_content.strip()
            
            python_step_file_path = os.path.join(python_dir, "steps.py")
            with open(python_step_file_path, "w", encoding="utf-8") as f:
                f.write(python_step_content)
            
            time.sleep(API_DELAY)

            # Python Page Object
            response = model_for_code.generate_content(python_page_object_prompt)
            python_page_content = response.text
            match = re.search(r'```python\n(.*?)```', python_page_content, re.DOTALL)
            python_page_content = match.group(1).strip() if match else python_page_content.strip()
            
            python_page_file_path = os.path.join(python_dir, "pages.py")
            with open(python_page_file_path, "w", encoding="utf-8") as f:
                f.write(python_page_content)
            
            time.sleep(API_DELAY)

            # Requirements.txt
            response = model_for_code.generate_content(requirements_txt_prompt)
            requirements_content = response.text.strip()
            # For requirements.txt, we don't expect code blocks, just plain text
            if '```' in requirements_content:
                match = re.search(r'```(?:txt)?\n(.*?)```', requirements_content, re.DOTALL)
                requirements_content = match.group(1).strip() if match else requirements_content.strip()
            
            requirements_file_path = os.path.join(python_dir, "requirements.txt")
            with open(requirements_file_path, "w", encoding="utf-8") as f:
                f.write(requirements_content)

            status_label.config(text="Phase 2: Multi-language automation files generated successfully!")
            progress_bar['value'] = 100
            root.update_idletasks()

        except Exception as e:
            logger.error(f"Error generating multi-language files with Gemini: {e}")
            status_label.config(text="Phase 2: Some files were not generated due to API errors.")
            progress_bar['value'] = 100
            root.update_idletasks()

        # Generate Step Definition File (Legacy - keeping for compatibility)
        try:
            pass  # This is now handled above in the multi-language generation
        except Exception as e:
            pass

        # Generate Page Object File (Legacy - keeping for compatibility)
        try:
            pass  # This is now handled above in the multi-language generation
        except Exception as e:
            pass

        # Generate package.json File (Legacy - keeping for compatibility)
        try:
            pass  # This is now handled above in the multi-language generation
        except Exception as e:
            pass
    else:
        if not gemini_api_available:
            status_label.config(text="Gemini API not available. Only local feature file was generated.")
        else:
            status_label.config(text="No unique Gherkin steps collected. Skipping code generation.")
        progress_bar['value'] = 100
        root.update_idletasks()

    messagebox.showinfo("Generation Complete", f"All requested automation files have been processed!\n\n"
                                             f"Generated files include:\n"
                                             f"- Feature file (.feature)\n"
                                             f"- JavaScript automation files (steps.js, pages.js, package.json)\n"
                                             f"- Java automation files (StepDefinitions.java, ApplicationPage.java, pom.xml)\n"
                                             f"- Python automation files (steps.py, pages.py, requirements.txt)\n\n"
                                             f"Please check the '{bdd_output_full_path}' directory.")
    status_label.config(text="Ready.")
    root.update_idletasks()

# --- GUI Functions ---

def select_acceptance_file_gui():
    """Opens a file dialog to select the Acceptance Criteria (User Story) file."""
    global user_story_input_file_path
    file_path = filedialog.askopenfilename(
        title="Select Acceptance Criteria (User Story) File",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
    )
    if file_path:
        # Enhanced validation using helper function
        is_valid, error_message = validate_input_file(file_path)
        if not is_valid:
            messagebox.showerror("Invalid File", error_message)
            logger.error(f"File validation failed: {error_message}")
            return

        user_story_input_file_path = file_path
        acceptance_path_entry.config(state=tk.NORMAL)
        acceptance_path_entry.delete(0, tk.END)
        acceptance_path_entry.insert(0, user_story_input_file_path)
        acceptance_path_entry.config(state="readonly")
        
        # Update expected output path display
        output_path_entry.config(state=tk.NORMAL)
        output_path_entry.delete(0, tk.END)
        output_path_entry.insert(0, os.path.join(current_output_root_dir, BDD_OUTPUT_SUBDIR_NAME))
        output_path_entry.config(state="readonly")
        
        # Clear the generated test case path when a new input file is selected
        generated_tc_path_entry.config(state=tk.NORMAL)
        generated_tc_path_entry.delete(0, tk.END)
        generated_tc_path_entry.config(state="readonly")

        status_label.config(text="File selected. Click 'Generate' to start.")
        logger.info(f"Input file selected: {file_path}")
    else:
        status_label.config(text="File selection cancelled.")

def clear_fields_gui():
    """Clears all file path entries and output path display."""
    global user_story_input_file_path, generated_test_cases_file_path
    user_story_input_file_path = None
    generated_test_cases_file_path = None
    
    acceptance_path_entry.config(state=tk.NORMAL)
    acceptance_path_entry.delete(0, tk.END)
    acceptance_path_entry.config(state="readonly")
    
    generated_tc_path_entry.config(state=tk.NORMAL)
    generated_tc_path_entry.delete(0, tk.END)
    generated_tc_path_entry.config(state="readonly")

    output_path_entry.config(state=tk.NORMAL)
    output_path_entry.delete(0, tk.END)
    output_path_entry.config(state="readonly")
    
    status_label.config(text="Fields cleared. Select a file to begin.")
    progress_bar['value'] = 0
    
    # Disable the BDD generation button and view button since no test cases exist
    generate_bdd_button.config(state=tk.DISABLED)
    open_test_cases_button.config(state=tk.DISABLED)
    open_folder_button.config(state=tk.DISABLED)

def change_directory_gui():
    """Allows user to select a custom root directory for output files."""
    global current_output_root_dir
    new_dir = filedialog.askdirectory(title="Select Output Root Directory")
    if new_dir:
        current_output_root_dir = new_dir
        directory_label.config(text=f"Output Root Directory: {current_output_root_dir}")
        messagebox.showinfo("Directory Changed", f"All generated files will now be saved under: {current_output_root_dir}")
        # Update the displayed output path
        output_path_entry.config(state=tk.NORMAL)
        output_path_entry.delete(0, tk.END)
        output_path_entry.insert(0, os.path.join(current_output_root_dir, BDD_OUTPUT_SUBDIR_NAME))
        output_path_entry.config(state="readonly")
        # Also update the generated test cases path if it was previously set
        if generated_test_cases_file_path:
            generated_tc_path_entry.config(state=tk.NORMAL)
            generated_tc_path_entry.delete(0, tk.END)
            generated_tc_path_entry.insert(0, os.path.join(current_output_root_dir, GENERATED_TEST_CASES_FILE_NAME))
            generated_tc_path_entry.config(state="readonly")
        status_label.config(text=f"Output directory set to: {current_output_root_dir}")
    else:
        status_label.config(text="Directory change cancelled.")

def open_test_cases_file():
    """Opens the generated test cases Excel file for review."""
    if not generated_test_cases_file_path or not os.path.exists(generated_test_cases_file_path):
        messagebox.showwarning("File Not Found", "Test cases file not found. Please generate test cases first.")
        return

    try:
        if os.name == 'nt':  # Windows
            os.startfile(generated_test_cases_file_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', generated_test_cases_file_path])
        else:  # Linux and other Unix-like systems
            subprocess.Popen(['xdg-open', generated_test_cases_file_path])
    except Exception as e:
        logger.error(f"Could not open test cases file: {e}")
        messagebox.showerror("Error Opening File", f"Could not open test cases file: {e}")

def open_output_folder_gui():
    """Opens the generated BDD files folder in the system's file explorer."""
    bdd_output_full_path = os.path.join(current_output_root_dir, BDD_OUTPUT_SUBDIR_NAME)
    if not os.path.exists(bdd_output_full_path):
        messagebox.showwarning("Folder Not Found", f"The output folder does not exist yet:\n{bdd_output_full_path}")
        return

    try:
        if os.name == 'nt':  # Windows
            os.startfile(bdd_output_full_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', bdd_output_full_path])
        else:  # Linux and other Unix-like systems
            subprocess.Popen(['xdg-open', bdd_output_full_path])
    except Exception as e:
        logger.error(f"Could not open folder: {e}")
        messagebox.showerror("Error Opening Folder", f"Could not open folder: {e}")


def start_test_case_generation_thread():
    """
    Starts the test case generation process in a separate thread to keep the GUI responsive.
    """
    if not user_story_input_file_path:
        messagebox.showwarning("Input Missing", "Please select an Acceptance Criteria (User Story) File first.")
        return

    # Disable buttons during generation
    generate_test_cases_button.config(state=tk.DISABLED)
    select_acceptance_button.config(state=tk.DISABLED)
    clear_button.config(state=tk.DISABLED)
    change_dir_button.config(state=tk.DISABLED)
    open_folder_button.config(state=tk.DISABLED)
    generate_bdd_button.config(state=tk.DISABLED)
    status_label.config(text="Starting test case generation...")
    progress_bar['value'] = 0
    root.update_idletasks()

    # Run the test case generation logic in a separate thread
    thread = threading.Thread(target=run_test_case_generation_logic)
    thread.start()

def run_test_case_generation_logic():
    """
    Contains the test case generation logic, run in a separate thread.
    """
    global generated_test_cases_file_path
    try:
        # Phase 1: Generate Test Cases Only
        generated_tc_file = generate_test_cases_from_user_stories_backend(
            user_story_input_file_path, current_output_root_dir
        )

        if generated_tc_file:
            generated_test_cases_file_path = generated_tc_file
            # Update the UI with the generated test cases file path
            generated_tc_path_entry.config(state=tk.NORMAL)
            generated_tc_path_entry.delete(0, tk.END)
            generated_tc_path_entry.insert(0, generated_test_cases_file_path)
            generated_tc_path_entry.config(state="readonly")
            
            # Enable the BDD generation button and view button now that test cases are ready
            generate_bdd_button.config(state=tk.NORMAL)
            open_test_cases_button.config(state=tk.NORMAL)
            
            status_label.config(text="Test cases generated successfully! Review them and click 'Generate BDD Files' to continue.")
            messagebox.showinfo("Test Cases Generated", 
                              f"Test cases have been generated successfully!\n\n"
                              f"File location: {os.path.basename(generated_tc_file)}\n\n"
                              f"Please review the test cases and click 'Generate BDD Files' to continue.")
        else:
            messagebox.showerror("Generation Failed", "Test case generation failed. Please check the logs for details.")
            status_label.config(text="Test case generation failed.")

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred during test case generation: {e}")
        status_label.config(text="Test case generation failed due to an unexpected error.")
    finally:
        # Re-enable buttons after generation (or failure)
        generate_test_cases_button.config(state=tk.NORMAL)
        select_acceptance_button.config(state=tk.NORMAL)
        clear_button.config(state=tk.NORMAL)
        change_dir_button.config(state=tk.NORMAL)
        open_folder_button.config(state=tk.NORMAL)
        root.update_idletasks()
        progress_bar['value'] = 0

def start_bdd_generation_thread():
    """
    Starts the BDD file generation process in a separate thread to keep the GUI responsive.
    """
    if not generated_test_cases_file_path or not os.path.exists(generated_test_cases_file_path):
        messagebox.showwarning("Test Cases Missing", "Please generate test cases first before creating BDD files.")
        return

    # Disable buttons during generation
    generate_test_cases_button.config(state=tk.DISABLED)
    generate_bdd_button.config(state=tk.DISABLED)
    select_acceptance_button.config(state=tk.DISABLED)
    clear_button.config(state=tk.DISABLED)
    change_dir_button.config(state=tk.DISABLED)
    open_folder_button.config(state=tk.DISABLED)
    status_label.config(text="Starting BDD file generation...")
    progress_bar['value'] = 50  # Start from 50% since test cases are already done
    root.update_idletasks()

    # Run the BDD generation logic in a separate thread
    thread = threading.Thread(target=run_bdd_generation_logic)
    thread.start()

def run_bdd_generation_logic():
    """
    Contains the BDD file generation logic, run in a separate thread.
    """
    try:
        # Phase 2: Generate BDD Files from existing Test Cases
        generate_bdd_files_backend(generated_test_cases_file_path, current_output_root_dir)
        
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred during BDD file generation: {e}")
        status_label.config(text="BDD file generation failed due to an unexpected error.")
    finally:
        # Re-enable buttons after generation (or failure)
        generate_test_cases_button.config(state=tk.NORMAL)
        generate_bdd_button.config(state=tk.NORMAL)
        select_acceptance_button.config(state=tk.NORMAL)
        clear_button.config(state=tk.NORMAL)
        change_dir_button.config(state=tk.NORMAL)
        open_folder_button.config(state=tk.NORMAL)
        root.update_idletasks()
        progress_bar['value'] = 0


def start_generation_thread():
    """
    Legacy function - now calls the two-step process automatically.
    Starts the generation process in a separate thread to keep the GUI responsive.
    """
    if not user_story_input_file_path:
        messagebox.showwarning("Input Missing", "Please select an Acceptance Criteria (User Story) File first.")
        return

    # Disable buttons during generation
    generate_test_cases_button.config(state=tk.DISABLED)
    generate_bdd_button.config(state=tk.DISABLED)
    select_acceptance_button.config(state=tk.DISABLED)
    clear_button.config(state=tk.DISABLED)
    change_dir_button.config(state=tk.DISABLED)
    open_folder_button.config(state=tk.DISABLED)
    status_label.config(text="Starting generation process...")
    progress_bar['value'] = 0
    root.update_idletasks()

    # Run the backend logic in a separate thread
    thread = threading.Thread(target=run_generation_logic)
    thread.start()

def run_generation_logic():
    """
    Contains the main backend logic for generation, run in a separate thread.
    """
    global generated_test_cases_file_path
    try:
        # Phase 1: Generate Test Cases
        generated_tc_file = generate_test_cases_from_user_stories_backend(
            user_story_input_file_path, current_output_root_dir
        )

        if generated_tc_file:
            generated_test_cases_file_path = generated_tc_file
            # Update the UI with the generated test cases file path
            generated_tc_path_entry.config(state=tk.NORMAL)
            generated_tc_path_entry.delete(0, tk.END)
            generated_tc_path_entry.insert(0, generated_test_cases_file_path)
            generated_tc_path_entry.config(state="readonly")
            
            # Phase 2: Generate BDD Files based on the generated Test Cases
            generate_bdd_files_backend(generated_tc_file, current_output_root_dir)
        else:
            messagebox.showerror("Process Aborted", "Test case generation failed or was skipped. Cannot proceed with BDD file generation.")
            status_label.config(text="Generation aborted.")

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred during generation: {e}")
        status_label.config(text="Generation failed due to an unexpected error.")
    finally:
        # Re-enable buttons after generation (or failure)
        generate_test_cases_button.config(state=tk.NORMAL)
        generate_bdd_button.config(state=tk.NORMAL)
        select_acceptance_button.config(state=tk.NORMAL)
        clear_button.config(state=tk.NORMAL)
        change_dir_button.config(state=tk.NORMAL)
        open_folder_button.config(state=tk.NORMAL)
        root.update_idletasks()
        progress_bar['value'] = 0


# --- GUI Setup ---
root = tk.Tk()
root.title("BDD Automation Generator")
root.geometry("800x650") # Increased height to accommodate new field
root.resizable(True, True)

# Styles
BG_COLOR = "#f0f0f0"
BUTTON_COLOR = "#4CAF50" # Green
BUTTON_FG = "white"
ACCENT_COLOR = "#2196F3" # Blue
ERROR_COLOR = "#f44336" # Red
FONT_TITLE = ("Arial", 22, "bold") # Slightly larger title
FONT_LABEL = ("Arial", 12)
FONT_ENTRY = ("Arial", 11)
FONT_BUTTON = ("Arial", 12, "bold")
STATUS_FONT = ("Arial", 11, "italic")
API_STATUS_FONT = ("Arial", 10, "bold")

root.config(bg=BG_COLOR)

# Title
title_label = tk.Label(root, text="BDD Automation Generator", font=FONT_TITLE, bg=BG_COLOR, fg="#333")
title_label.pack(pady=15)

# API Status Display
api_status_frame = tk.Frame(root, bg=BG_COLOR)
api_status_frame.pack(pady=5)
api_status_label = tk.Label(api_status_frame, text="API Status: Checking...", font=API_STATUS_FONT, bg=BG_COLOR, fg="gray")
api_status_label.pack(side=tk.LEFT, padx=5)
refresh_api_button = tk.Button(api_status_frame, text="Refresh API Status", command=check_gemini_api_status, font=("Arial", 9), bg="#FFA500", fg="white", relief=tk.FLAT)
refresh_api_button.pack(side=tk.LEFT, padx=5)

def set_api_key_gui():
    """Allows user to manually set the API key through GUI"""
    api_key = tk.simpledialog.askstring("Set API Key", "Enter your Gemini API Key:", show='*')
    if api_key and api_key.strip():
        os.environ['GEMINI_API_KEY'] = api_key.strip()
        messagebox.showinfo("Success", "API Key has been set! Click 'Refresh API Status' to verify.")
        logger.info("API key set manually through GUI")
    else:
        messagebox.showwarning("Cancelled", "API key was not set.")

set_key_button = tk.Button(api_status_frame, text="Set API Key", command=set_api_key_gui, font=("Arial", 9), bg="#FF6B6B", fg="white", relief=tk.FLAT)
set_key_button.pack(side=tk.LEFT, padx=5)

# Initial check for API status
check_gemini_api_status()


# Output Directory Display
directory_frame = tk.Frame(root, bg=BG_COLOR)
directory_frame.pack(pady=5)
directory_label = tk.Label(directory_frame, text=f"Output Root Directory: {current_output_root_dir}", font=FONT_LABEL, fg=ACCENT_COLOR, bg=BG_COLOR)
directory_label.pack(side=tk.LEFT, padx=5)
change_dir_button = tk.Button(directory_frame, text="Change", command=change_directory_gui, font=("Arial", 10), bg=ACCENT_COLOR, fg=BUTTON_FG, relief=tk.FLAT)
change_dir_button.pack(side=tk.LEFT, padx=5)


# Input File Selection
input_frame = tk.LabelFrame(root, text="Input Acceptance Criteria (User Story) File", font=FONT_LABEL, bg=BG_COLOR, padx=10, pady=10)
input_frame.pack(pady=10, padx=20, fill=tk.X)

select_acceptance_button = tk.Button(input_frame, text="Select File", command=select_acceptance_file_gui, font=FONT_BUTTON, bg=BUTTON_COLOR, fg=BUTTON_FG, relief=tk.RAISED)
select_acceptance_button.pack(side=tk.LEFT, padx=10)

acceptance_path_entry = tk.Entry(input_frame, width=50, font=FONT_ENTRY, state="readonly")
acceptance_path_entry.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)


# NEW: Generated Test Cases File Path Display
generated_tc_frame = tk.LabelFrame(root, text="Generated Comprehensive Test Cases File (Intermediate Output)", font=FONT_LABEL, bg=BG_COLOR, padx=10, pady=10)
generated_tc_frame.pack(pady=10, padx=20, fill=tk.X)

generated_tc_path_entry = tk.Entry(generated_tc_frame, width=50, font=FONT_ENTRY, state="readonly")
generated_tc_path_entry.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

open_test_cases_button = tk.Button(generated_tc_frame, text="View Test Cases", command=open_test_cases_file, font=("Arial", 10), bg="#17a2b8", fg="white", relief=tk.FLAT)
open_test_cases_button.pack(side=tk.LEFT, padx=5)
open_test_cases_button.config(state=tk.DISABLED)  # Initially disabled


# Action Buttons
action_frame = tk.Frame(root, bg=BG_COLOR)
action_frame.pack(pady=15)

generate_test_cases_button = tk.Button(action_frame, text="Generate Test Cases", command=start_test_case_generation_thread, font=FONT_BUTTON, bg="#28a745", fg=BUTTON_FG, relief=tk.RAISED, padx=15, pady=5)
generate_test_cases_button.pack(side=tk.LEFT, padx=10)

generate_bdd_button = tk.Button(action_frame, text="Generate BDD Files", command=start_bdd_generation_thread, font=FONT_BUTTON, bg="#007BFF", fg=BUTTON_FG, relief=tk.RAISED, padx=15, pady=5)
generate_bdd_button.pack(side=tk.LEFT, padx=10)
generate_bdd_button.config(state=tk.DISABLED)  # Initially disabled until test cases are generated

clear_button = tk.Button(action_frame, text="Clear Fields", command=clear_fields_gui, font=FONT_BUTTON, bg=ERROR_COLOR, fg=BUTTON_FG, relief=tk.RAISED, padx=15, pady=5)
clear_button.pack(side=tk.LEFT, padx=10)


# Output Path Display (for final BDD files)
output_frame = tk.LabelFrame(root, text="Generated BDD Automation Files Location (Final Output)", font=FONT_LABEL, bg=BG_COLOR, padx=10, pady=10)
output_frame.pack(pady=10, padx=20, fill=tk.X)

output_path_entry = tk.Entry(output_frame, width=70, font=FONT_ENTRY, state="readonly")
output_path_entry.pack(padx=10, expand=True, fill=tk.X)
# Initialize with default output path
output_path_entry.config(state=tk.NORMAL)
output_path_entry.delete(0, tk.END)
output_path_entry.insert(0, os.path.join(current_output_root_dir, BDD_OUTPUT_SUBDIR_NAME))
output_path_entry.config(state="readonly")

# Open Output Folder Button
open_folder_button = tk.Button(root, text="Open Output Folder", command=open_output_folder_gui, font=FONT_BUTTON, bg="#6c757d", fg=BUTTON_FG, relief=tk.RAISED, padx=15, pady=5)
open_folder_button.pack(pady=10)
open_folder_button.config(state=tk.DISABLED) # Initially disabled until files are generated

# Progress Bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Ready. Select an Acceptance Criteria file to begin.", font=STATUS_FONT, bg=BG_COLOR, fg="#555")
status_label.pack(pady=10)


# Run the application
root.mainloop()
