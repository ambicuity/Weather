#!/usr/bin/env python3
"""
Main update script for GitHub profile README
Orchestrates all dynamic content generation and README updates
"""

import os
import sys
import subprocess
from datetime import datetime

def run_script(script_name):
    """Run a Python script and return its output"""
    try:
        result = subprocess.run([sys.executable, f'scripts/{script_name}'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print(f"✅ {script_name} executed successfully")
            return True
        else:
            print(f"❌ {script_name} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def read_file_content(filename):
    """Read content from a file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return f.read()
        return ""
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return ""

def update_readme():
    """Update README.md with all dynamic content"""
    try:
        # Read current README or create template
        readme_path = 'README.md'
        
        # Define the new README template with all sections
        readme_template = """# Dynamic GitHub Profile README

<!-- HEADER-START -->
{header_content}
<!-- HEADER-END -->

<!-- QUOTES-START -->
{quotes_content}
<!-- QUOTES-END -->

<!-- VISITOR-COUNTER-START -->
{visitor_content}
<!-- VISITOR-COUNTER-END -->

<!-- AGE-START -->
{age_content}
<!-- AGE-END -->

<!-- TYPING-ANIMATION-START -->
{typing_content}
<!-- TYPING-ANIMATION-END -->

<!-- LEETCODE-START -->
{leetcode_content}
<!-- LEETCODE-END -->

<!-- WEATHER-START -->
{weather_content}
<!-- WEATHER-END -->

## 🛠️ Tech Stack

<p align="center">
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
    <img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="GitHub Actions">
    <img src="https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white" alt="Markdown">
</p>

## 📈 GitHub Stats

<p align="center">
    <img src="https://github-readme-stats.vercel.app/api?username=ambicuity&show_icons=true&theme=radical" alt="GitHub Stats">
</p>

---

<p align="center">
    <i>This README is automatically updated using GitHub Actions</i><br>
    <i>Last updated: {timestamp}</i>
</p>
"""

        # Read generated content from each script
        header_content = read_file_content('header_display.html')
        quotes_content = read_file_content('daily_content.html')
        visitor_content = read_file_content('visitor_counter.html')
        age_content = read_file_content('age_display.html')
        typing_content = read_file_content('typing_animation.html')
        leetcode_content = read_file_content('leetcode_progress.html')
        weather_content = read_file_content('weather_data.html')
        
        # Format README with current content
        new_readme = readme_template.format(
            header_content=header_content,
            quotes_content=quotes_content,
            visitor_content=visitor_content,
            age_content=age_content,
            typing_content=typing_content,
            leetcode_content=leetcode_content,
            weather_content=weather_content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        # Write updated README
        with open(readme_path, 'w') as f:
            f.write(new_readme)
        
        print("✅ README.md updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating README: {e}")
        return False

def main():
    """Main function to orchestrate all updates"""
    print("🚀 Starting GitHub profile README update...")
    
    # List of scripts to run
    scripts = [
        'header_generator.py',
        'quotes.py',
        'visitor_counter.py',
        'age_calculator.py',
        'typing_animation.py',
        'leetcode_progress.py',
        'weather.py'
    ]
    
    # Run all scripts
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
    
    print(f"\n📊 Script execution summary: {success_count}/{len(scripts)} successful")
    
    # Update README with all generated content
    if update_readme():
        print("✅ Profile README update completed successfully!")
    else:
        print("❌ Failed to update README")
        sys.exit(1)

if __name__ == "__main__":
    main()