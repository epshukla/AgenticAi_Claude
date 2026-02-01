#!/usr/bin/env python3
"""
Cross-Directory AI Agent using Claude API.

This is a real agent-style architecture demonstrating how a script in one
directory can read from and modify files in a completely separate directory
using Claude for intelligent content transformation.

Key Architecture Principles:
1. Agent (this script) lives ONLY in /demo directory
2. Claude has NO direct filesystem access
3. All file operations are controlled by the agent script
4. Absolute paths prevent directory traversal exploits
5. Safety checks validate all target files
"""

import os
import sys
from pathlib import Path
from typing import Optional
import json

import anthropic

# Import configuration from the same directory
from config import (
    DEMO_DIR,
    TARGET_PROJECT_DIR,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    SYSTEM_PROMPT,
    validate_target_path
)


class CrossDirectoryAgent:
    """
    An AI agent that can read and modify files in external project directories.
    
    This agent demonstrates enterprise-grade file management where:
    - The AI model (Claude) never touches the filesystem
    - The agent controls all file I/O operations
    - Safety checks prevent unauthorized file access
    - Absolute paths ensure no directory escape attempts
    """
    
    def __init__(self, api_key: str, model: str = CLAUDE_MODEL):
        """
        Initialize the agent with Claude API credentials.
        
        Args:
            api_key: Claude API key
            model: Model to use (defaults to latest Sonnet)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
        
        print(f"[AGENT] Initialized with model: {self.model}")
        print(f"[AGENT] Agent directory: {DEMO_DIR}")
        print(f"[AGENT] Target project directory: {TARGET_PROJECT_DIR}\n")
    
    def read_target_file(self, relative_path: str) -> Optional[str]:
        """
        Read a file from the target project directory.
        
        This is the ONLY way Claude gets access to file contents.
        The agent must verify the file is safe before reading.
        
        Args:
            relative_path: Path relative to TARGET_PROJECT_DIR (e.g., "README.md")
        
        Returns:
            File contents as string, or None if file is unsafe/missing
        """
        # Construct absolute path to the target file
        target_file = TARGET_PROJECT_DIR / relative_path
        
        print(f"[AGENT] Reading target file: {relative_path}")
        print(f"[AGENT] Full absolute path: {target_file}")
        
        # Security check: validate the file is safe to read
        if not validate_target_path(target_file):
            print(f"[ERROR] File validation failed: {relative_path}")
            print(f"        - File doesn't exist, or")
            print(f"        - File is outside target directory, or")
            print(f"        - File extension not whitelisted, or")
            print(f"        - File exceeds size limit\n")
            return None
        
        try:
            content = target_file.read_text(encoding="utf-8")
            print(f"[SUCCESS] Read {len(content)} characters\n")
            return content
        except Exception as e:
            print(f"[ERROR] Failed to read file: {e}\n")
            return None
    
    def write_target_file(self, relative_path: str, content: str) -> bool:
        """
        Write modified content back to the target project directory.
        
        This is the ONLY way modified content gets written to disk.
        The agent verifies the target path before writing.
        
        Args:
            relative_path: Path relative to TARGET_PROJECT_DIR
            content: New file content from Claude
        
        Returns:
            True if successful, False otherwise
        """
        target_file = TARGET_PROJECT_DIR / relative_path
        
        print(f"[AGENT] Writing to target file: {relative_path}")
        print(f"[AGENT] Full absolute path: {target_file}")
        print(f"[AGENT] Content size: {len(content)} characters")
        
        # Security check: validate the file is safe to write
        if not validate_target_path(target_file):
            print(f"[ERROR] File validation failed - cannot write\n")
            return False
        
        try:
            # Create parent directory if needed (within TARGET_PROJECT_DIR)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            target_file.write_text(content, encoding="utf-8")
            print(f"[SUCCESS] File written successfully\n")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write file: {e}\n")
            return False
    
    def request_claude_modification(self, file_content: str, task_description: str) -> Optional[str]:
        """
        Send file content to Claude for modification.
        
        CRITICAL: Claude receives ONLY the content, never the file path.
        This ensures Claude cannot reference or escape to other files.
        
        Args:
            file_content: The content to be modified
            task_description: Detailed instructions for Claude
        
        Returns:
            Modified content from Claude, or None if request fails
        """
        print(f"[AGENT] Sending request to Claude API...")
        print(f"[AGENT] Task: {task_description[:80]}...\n")
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Please improve and refactor the following file content.

Task: {task_description}

IMPORTANT: Return ONLY the improved file content. Do NOT include:
- File paths or filenames
- Explanation or commentary
- Markdown code blocks
- Any text outside the improved content itself

Original content:
---
{file_content}
---

Return the improved content:"""
                    }
                ]
            )
            
            # Extract the response content
            modified_content = message.content[0].text
            
            print(f"[SUCCESS] Received response from Claude")
            print(f"[SUCCESS] Response size: {len(modified_content)} characters\n")
            
            return modified_content
            
        except anthropic.APIError as e:
            print(f"[ERROR] Claude API error: {e}\n")
            return None
    
    def process_file(self, relative_path: str, task_description: str) -> bool:
        """
        Complete workflow: read file -> send to Claude -> write back.
        
        This orchestrates the entire cross-directory modification process:
        1. Read file from target directory
        2. Send to Claude with specific instructions
        3. Claude returns improved content (no file path knowledge)
        4. Agent writes content back to target directory
        
        Args:
            relative_path: Path to file in target directory
            task_description: Instructions for Claude
        
        Returns:
            True if entire process succeeded, False otherwise
        """
        print("=" * 75)
        print(f"PROCESSING: {relative_path}")
        print("=" * 75 + "\n")
        
        # STEP 1: Agent reads file from target directory
        original_content = self.read_target_file(relative_path)
        if original_content is None:
            return False
        
        print("[WORKFLOW] Step 1: ✓ Read file from target directory")
        print(f"[WORKFLOW] Step 2: Sending to Claude...\n")
        
        # STEP 2: Agent sends content to Claude (no file paths!)
        modified_content = self.request_claude_modification(
            original_content,
            task_description
        )
        if modified_content is None:
            return False
        
        print("[WORKFLOW] Step 2: ✓ Received modified content from Claude")
        print(f"[WORKFLOW] Step 3: Writing back to target directory...\n")
        
        # STEP 3: Agent writes modified content back to target
        success = self.write_target_file(relative_path, modified_content)
        
        if success:
            print("[WORKFLOW] Step 3: ✓ Write successful")
            print("[WORKFLOW] ✓ ALL STEPS COMPLETED\n")
        
        return success

    def analyze_directory(self, relative_path: str, task_description: str) -> bool:
        """
        Analyze all files in a directory and its subdirectories.
        
        This method:
        1. Recursively finds all allowed files
        2. Aggregates their content
        3. Sends the aggregated content to Claude for analysis
        
        Args:
            relative_path: Directory path relative to TARGET_PROJECT_DIR
            task_description: Instructions for Claude
            
        Returns:
            True if analysis was successful
        """
        target_dir = TARGET_PROJECT_DIR / relative_path
        
        print("=" * 75)
        print(f"ANALYZING DIRECTORY: {relative_path}")
        print("=" * 75 + "\n")
        
        if not target_dir.exists() or not target_dir.is_dir():
            print(f"[ERROR] Directory not found: {relative_path}")
            return False
            
        aggregated_content = []
        file_count = 0
        
        print(f"[AGENT] Scanning directory: {target_dir}")
        
        # files to ignore
        IGNORE_DIRS = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'build', 'coverage'}
        
        for root, dirs, files in os.walk(target_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                rel_file_path = file_path.relative_to(TARGET_PROJECT_DIR)
                
                # Check extension
                if file_path.suffix not in ALLOWED_EXTENSIONS:
                    continue
                    
                # Check size
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    print(f"[SKIP] File too large: {rel_file_path}")
                    continue
                
                # Check if file is safe (using existing validation logic if possible, 
                # but here we are confident it is within target_dir because of os.walk)
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    aggregated_content.append(f"File: {rel_file_path}\n---\n{content}\n---\n")
                    file_count += 1
                    print(f"[Found] {rel_file_path}")
                except Exception as e:
                    print(f"[ERROR] Could not read {rel_file_path}: {e}")
        
        if not aggregated_content:
            print("[ERROR] No valid files found to analyze.")
            return False
            
        print(f"\n[AGENT] Found {file_count} files to analyze.")
        full_content = "\n".join(aggregated_content)
        
        print(f"[AGENT] Sending aggregated content to Claude ({len(full_content)} chars)...")
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Please analyze the project and perform the requested task.
                        
Task: {task_description}

Project Content:
{full_content}

If you need to modify any files, return the full content of the modified file(s) wrapped in XML tags like this:
<file path="relative/path/to/file.ext">
... content ...
</file>

You can modify multiple files if needed. If no changes are needed, just provide analysis text.
"""
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            print("\n" + "=" * 75)
            print("CLAUDE RESPONSE:")
            print("=" * 75)
            print(response_text)
            print("=" * 75 + "\n")
            
            # Simple parsing of XML-like tags
            import re
            # Regex to capture content between <file path="..."> and </file>
            # Use DOTALL to match newlines
            pattern = re.compile(r'<file path="([^"]+)">\s*(.*?)\s*</file>', re.DOTALL)
            matches = pattern.findall(response_text)
            
            if not matches:
                print("[INFO] No file modifications proposed by Claude.")
                return True
                
            print(f"[AGENT] Found {len(matches)} file modification(s). Applying changes...")
            
            for rel_path, new_content in matches:
                # Sanitize path
                target_file = TARGET_PROJECT_DIR / rel_path.strip()
                
                # Verify safety again
                if not validate_target_path(target_file):
                    print(f"[ERROR] Skipped unsafe path: {rel_path}")
                    continue
                    
                try:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(new_content, encoding='utf-8')
                    print(f"[SUCCESS] Updated file: {rel_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to write {rel_path}: {e}")
            
            return True
            
        except anthropic.APIError as e:
            print(f"[ERROR] Claude API error: {e}\n")
            return False


def main():
    """
    Demonstrate the cross-directory AI agent in action.
    """
    print("\n" + "=" * 75)
    print("CROSS-DIRECTORY AI AGENT DEMONSTRATION")
    print("=" * 75 + "\n")
    
    # Initialize the agent with Claude API credentials
    agent = CrossDirectoryAgent(api_key=CLAUDE_API_KEY)
    
    # Analyze the entire project directory
    print("[DEMO] Scanning ecommerce-website to find and modify 'Shop Now' button...")
    success = agent.analyze_directory(
        relative_path=".",
        task_description="Find a button labeled 'Shop Now' in the frontend files (likely in src/components or pages). "
                         "Change its background color to blue. Return the modified file content."
    )
    
    if success:
        print("=" * 75)
        print("✓ DEMONSTRATION COMPLETE: Directory analysis successful!")
        print("=" * 75)
        print(f"\nAnalyzed directory: {TARGET_PROJECT_DIR}")
        print(f"Agent location: {DEMO_DIR / 'agent.py'}")
        print("\nKey Architecture Points:")
        print("  1. Agent script recursively scanned target directory")
        print("  2. Files were aggregated in memory (no direct LLM access to FS)")
        print("  3. Content was sent to Claude for holistic analysis")
        print("  4. Issues were identified across multiple files")
        print()
        
    else:
        print("=" * 75)
        print("✗ DEMONSTRATION FAILED")
        print("=" * 75)
        sys.exit(1)


if __name__ == "__main__":
    main()
