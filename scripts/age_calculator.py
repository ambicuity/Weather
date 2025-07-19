#!/usr/bin/env python3
"""
Dynamic age calculator for GitHub profile README
Calculates and displays current age automatically
"""

import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def calculate_age(birth_date_str):
    """Calculate age from birth date string (YYYY-MM-DD format)"""
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = date.today()
        
        # Calculate exact age
        age = relativedelta(today, birth_date)
        
        return {
            'years': age.years,
            'months': age.months,
            'days': age.days,
            'total_days': (today - birth_date).days
        }
    except Exception as e:
        print(f"Error calculating age: {e}")
        return None

def generate_age_display(age_data, name="Developer"):
    """Generate HTML display for dynamic age"""
    if not age_data:
        return "## 🎂 Age\n\nAge calculation unavailable"
    
    years = age_data['years']
    months = age_data['months']
    days = age_data['days']
    total_days = age_data['total_days']
    
    return f"""## 🎂 About Me

<p align="center">
    <img src="https://img.shields.io/badge/Age-{years}%20years%20{months}%20months%20{days}%20days-brightgreen?style=for-the-badge&logo=calendar&logoColor=white" alt="Current Age">
</p>

**🌟 I'm {years} years old and have been alive for {total_days:,} days!**

*Age updates automatically every day*
"""

def main():
    """Main function"""
    # Get birth date from environment variable or use default
    birth_date = os.getenv('BIRTH_DATE', '1995-01-01')  # Default birth date
    name = os.getenv('PROFILE_NAME', 'Developer')
    
    # Calculate age
    age_data = calculate_age(birth_date)
    
    # Generate display
    display = generate_age_display(age_data, name)
    
    # Save to file for use in README update
    with open('age_display.html', 'w') as f:
        f.write(display)
    
    if age_data:
        print(f"Age calculated: {age_data['years']} years, {age_data['months']} months, {age_data['days']} days")
    else:
        print("Failed to calculate age")
    
    return display

if __name__ == "__main__":
    main()