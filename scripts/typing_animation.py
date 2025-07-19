#!/usr/bin/env python3
"""
Typing animation SVG generator for GitHub profile README
Creates an SVG with typing animation effect
"""

import os
import xml.etree.ElementTree as ET

def create_typing_svg(text="Hello, I'm a Developer!", width=800, height=100):
    """Create SVG with typing animation"""
    
    # Create SVG root element
    svg = ET.Element('svg', {
        'width': str(width),
        'height': str(height),
        'xmlns': 'http://www.w3.org/2000/svg'
    })
    
    # Add background
    bg_rect = ET.SubElement(svg, 'rect', {
        'width': str(width),
        'height': str(height),
        'fill': '#0d1117',
        'rx': '10'
    })
    
    # Add text element with typing animation
    text_elem = ET.SubElement(svg, 'text', {
        'x': '20',
        'y': '60',
        'font-family': 'Monaco, "Courier New", monospace',
        'font-size': '24',
        'font-weight': 'bold',
        'fill': '#58a6ff'
    })
    text_elem.text = text
    
    # Add typing cursor
    cursor = ET.SubElement(svg, 'rect', {
        'x': str(20 + len(text) * 14),  # Approximate character width
        'y': '40',
        'width': '3',
        'height': '30',
        'fill': '#58a6ff'
    })
    
    # Add cursor blinking animation
    cursor_animate = ET.SubElement(cursor, 'animate', {
        'attributeName': 'opacity',
        'values': '1;0;1',
        'dur': '1s',
        'repeatCount': 'indefinite'
    })
    
    # Add typing effect animation
    text_animate = ET.SubElement(text_elem, 'animate', {
        'attributeName': 'opacity',
        'values': '0;1',
        'dur': '0.1s',
        'fill': 'freeze'
    })
    
    # Add character reveal animation
    for i, char in enumerate(text):
        if i == 0:
            continue
        char_animate = ET.SubElement(text_elem, 'animate', {
            'attributeName': 'textContent',
            'values': f'{text[:i]};{text[:i+1]}',
            'dur': '0.1s',
            'begin': f'{i * 0.1}s',
            'fill': 'freeze'
        })
    
    return svg

def save_svg_file(svg_element, filename):
    """Save SVG element to file"""
    try:
        # Convert to string and save
        svg_string = ET.tostring(svg_element, encoding='unicode')
        
        # Add XML declaration and format
        svg_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{svg_string}'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        return True
    except Exception as e:
        print(f"Error saving SVG: {e}")
        return False

def generate_typing_animation_display():
    """Generate display for typing animation"""
    return """## ⌨️ Typing Animation

<p align="center">
    <img src="./assets/typing_animation.svg" alt="Typing Animation" />
</p>
"""

def main():
    """Main function"""
    # Get text from environment or use default
    text = os.getenv('TYPING_TEXT', "Hello, I'm a Developer! 👨‍💻")
    
    # Create SVG
    svg = create_typing_svg(text)
    
    # Ensure assets directory exists
    os.makedirs('assets', exist_ok=True)
    
    # Save SVG file
    if save_svg_file(svg, 'assets/typing_animation.svg'):
        print("Typing animation SVG generated successfully!")
    else:
        print("Failed to generate typing animation SVG")
    
    # Generate display content
    display = generate_typing_animation_display()
    
    # Save display content
    with open('typing_animation.html', 'w') as f:
        f.write(display)
    
    return display

if __name__ == "__main__":
    main()