#!/usr/bin/env python3
"""
Custom header images generator for GitHub profile README
Creates personalized SVG headers with dynamic text
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
import random

def create_gradient_defs():
    """Create gradient definitions for background"""
    defs = ET.Element('defs')
    
    # Create linear gradient
    gradient = ET.SubElement(defs, 'linearGradient', {
        'id': 'headerGradient',
        'x1': '0%',
        'y1': '0%',
        'x2': '100%',
        'y2': '100%'
    })
    
    # Gradient colors
    colors = [
        ('#667eea', '0%'),
        ('#764ba2', '50%'),
        ('#f093fb', '100%')
    ]
    
    for color, offset in colors:
        ET.SubElement(gradient, 'stop', {
            'offset': offset,
            'stop-color': color
        })
    
    return defs

def create_header_svg(name="Developer", title="Full Stack Developer", status="Building Amazing Things", width=800, height=300):
    """Create custom header SVG"""
    
    # Create SVG root
    svg = ET.Element('svg', {
        'width': str(width),
        'height': str(height),
        'xmlns': 'http://www.w3.org/2000/svg'
    })
    
    # Add gradient definitions
    svg.append(create_gradient_defs())
    
    # Background with gradient
    bg_rect = ET.SubElement(svg, 'rect', {
        'width': str(width),
        'height': str(height),
        'fill': 'url(#headerGradient)',
        'rx': '15'
    })
    
    # Add decorative elements
    for i in range(5):
        circle = ET.SubElement(svg, 'circle', {
            'cx': str(random.randint(50, width-50)),
            'cy': str(random.randint(50, height-50)),
            'r': str(random.randint(20, 40)),
            'fill': 'rgba(255,255,255,0.1)'
        })
    
    # Main title
    name_text = ET.SubElement(svg, 'text', {
        'x': str(width // 2),
        'y': '80',
        'text-anchor': 'middle',
        'font-family': 'Arial, sans-serif',
        'font-size': '42',
        'font-weight': 'bold',
        'fill': 'white'
    })
    name_text.text = f"👋 Hi, I'm {name}!"
    
    # Subtitle
    title_text = ET.SubElement(svg, 'text', {
        'x': str(width // 2),
        'y': '130',
        'text-anchor': 'middle',
        'font-family': 'Arial, sans-serif',
        'font-size': '24',
        'fill': 'rgba(255,255,255,0.9)'
    })
    title_text.text = title
    
    # Status/current activity
    status_text = ET.SubElement(svg, 'text', {
        'x': str(width // 2),
        'y': '170',
        'text-anchor': 'middle',
        'font-family': 'Arial, sans-serif',
        'font-size': '18',
        'fill': 'rgba(255,255,255,0.8)'
    })
    status_text.text = f"🚀 {status}"
    
    # Current time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    time_text = ET.SubElement(svg, 'text', {
        'x': str(width - 20),
        'y': str(height - 20),
        'text-anchor': 'end',
        'font-family': 'Monaco, monospace',
        'font-size': '12',
        'fill': 'rgba(255,255,255,0.6)'
    })
    time_text.text = f"Last updated: {current_time}"
    
    # Add some tech icons (simplified)
    icons_y = 220
    icons = ['💻', '🌐', '⚡', '🎯', '🚀']
    icon_spacing = width // (len(icons) + 1)
    
    for i, icon in enumerate(icons):
        icon_text = ET.SubElement(svg, 'text', {
            'x': str(icon_spacing * (i + 1)),
            'y': str(icons_y),
            'text-anchor': 'middle',
            'font-family': 'Arial, sans-serif',
            'font-size': '24',
            'fill': 'rgba(255,255,255,0.8)'
        })
        icon_text.text = icon
    
    return svg

def save_svg_file(svg_element, filename):
    """Save SVG element to file"""
    try:
        svg_string = ET.tostring(svg_element, encoding='unicode')
        svg_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{svg_string}'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        return True
    except Exception as e:
        print(f"Error saving header SVG: {e}")
        return False

def generate_header_display():
    """Generate display for header image"""
    return """<p align="center">
    <img src="./assets/header.svg" alt="Profile Header" />
</p>

---
"""

def main():
    """Main function"""
    # Get configuration from environment
    name = os.getenv('PROFILE_NAME', 'Developer')
    title = os.getenv('PROFILE_TITLE', 'Full Stack Developer')
    status = os.getenv('PROFILE_STATUS', 'Building Amazing Things')
    
    # Create header SVG
    header_svg = create_header_svg(name, title, status)
    
    # Ensure assets directory exists
    os.makedirs('assets', exist_ok=True)
    
    # Save header SVG
    if save_svg_file(header_svg, 'assets/header.svg'):
        print("Header SVG generated successfully!")
    else:
        print("Failed to generate header SVG")
    
    # Generate display content
    display = generate_header_display()
    
    # Save display content
    with open('header_display.html', 'w') as f:
        f.write(display)
    
    return display

if __name__ == "__main__":
    main()