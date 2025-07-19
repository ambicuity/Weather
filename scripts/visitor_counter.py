#!/usr/bin/env python3
"""
Visitor counter for GitHub profile README
Maintains a simple file-based visitor counter
"""

import os
import json
from datetime import datetime

COUNTER_FILE = 'visitor_count.json'

def load_counter():
    """Load visitor counter from file"""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                data = json.load(f)
                return data.get('count', 0), data.get('last_updated', '')
        except Exception as e:
            print(f"Error loading counter: {e}")
            return 0, ''
    return 0, ''

def save_counter(count):
    """Save visitor counter to file"""
    try:
        data = {
            'count': count,
            'last_updated': datetime.now().isoformat()
        }
        with open(COUNTER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving counter: {e}")
        return False

def increment_counter():
    """Increment the visitor counter"""
    count, last_updated = load_counter()
    new_count = count + 1
    
    if save_counter(new_count):
        return new_count
    else:
        return count

def generate_counter_display(count):
    """Generate HTML display for visitor counter"""
    return f"""## 👀 Profile Views

<p align="center">
    <img src="https://img.shields.io/badge/Profile%20Views-{count}-blue?style=for-the-badge&logo=eye&logoColor=white" alt="Profile Views">
</p>

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""

def main():
    """Main function"""
    # Increment counter (simulating a profile view)
    count = increment_counter()
    
    # Generate display
    display = generate_counter_display(count)
    
    # Save to file for use in README update
    with open('visitor_counter.html', 'w') as f:
        f.write(display)
    
    print(f"Visitor counter updated: {count} views")
    return display

if __name__ == "__main__":
    main()