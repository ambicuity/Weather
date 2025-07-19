#!/usr/bin/env python3
"""
LeetCode progress tracker for GitHub profile README
Tracks and displays coding challenge progress
"""

import os
import json
import requests
from datetime import datetime, date

PROGRESS_FILE = 'leetcode_progress.json'

def load_progress():
    """Load LeetCode progress from file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading progress: {e}")
            return create_default_progress()
    return create_default_progress()

def create_default_progress():
    """Create default progress structure"""
    return {
        'total_solved': 150,
        'easy_solved': 80,
        'medium_solved': 55,
        'hard_solved': 15,
        'current_streak': 5,
        'max_streak': 23,
        'last_solved': str(date.today()),
        'favorite_topics': ['Array', 'String', 'Dynamic Programming', 'Tree'],
        'recent_problems': [
            {'name': 'Two Sum', 'difficulty': 'Easy', 'date': '2024-01-15'},
            {'name': 'Add Two Numbers', 'difficulty': 'Medium', 'date': '2024-01-14'},
            {'name': 'Longest Substring', 'difficulty': 'Medium', 'date': '2024-01-13'}
        ]
    }

def save_progress(progress):
    """Save progress to file"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving progress: {e}")
        return False

def simulate_daily_progress(progress):
    """Simulate daily progress (increment counters)"""
    # Check if we need to update today
    today = str(date.today())
    if progress.get('last_solved') != today:
        # Simulate solving a problem (not every day)
        import random
        if random.random() < 0.7:  # 70% chance of solving a problem today
            progress['total_solved'] += 1
            
            # Randomly assign difficulty
            difficulty = random.choice(['easy', 'medium', 'hard'])
            progress[f'{difficulty}_solved'] += 1
            
            # Update streak
            progress['current_streak'] += 1
            if progress['current_streak'] > progress['max_streak']:
                progress['max_streak'] = progress['current_streak']
            
            # Add a recent problem
            problem_names = [
                'Binary Search', 'Merge Sort', 'Quick Sort', 'DFS Traversal',
                'BFS Traversal', 'Sliding Window', 'Two Pointers', 'Kadane\'s Algorithm',
                'Dijkstra\'s Algorithm', 'Backtracking', 'Dynamic Programming', 'Greedy Algorithm'
            ]
            new_problem = {
                'name': random.choice(problem_names),
                'difficulty': difficulty.capitalize(),
                'date': today
            }
            progress['recent_problems'].insert(0, new_problem)
            progress['recent_problems'] = progress['recent_problems'][:5]  # Keep only last 5
        else:
            # No problem solved today, might break streak
            if random.random() < 0.3:  # 30% chance of breaking streak
                progress['current_streak'] = 0
        
        progress['last_solved'] = today
    
    return progress

def generate_progress_display(progress):
    """Generate HTML display for LeetCode progress"""
    total = progress['total_solved']
    easy = progress['easy_solved']
    medium = progress['medium_solved']
    hard = progress['hard_solved']
    streak = progress['current_streak']
    max_streak = progress['max_streak']
    
    display = f"""## 🧩 LeetCode Progress

<p align="center">
    <img src="https://img.shields.io/badge/Total%20Solved-{total}-brightgreen?style=for-the-badge&logo=leetcode&logoColor=white" alt="Total Solved">
    <img src="https://img.shields.io/badge/Current%20Streak-{streak}%20days-orange?style=for-the-badge&logo=fire&logoColor=white" alt="Current Streak">
</p>

### 📊 Problem Breakdown

| Difficulty | Solved | Percentage |
|------------|--------|------------|
| 🟢 Easy | {easy} | {(easy/total*100):.1f}% |
| 🟡 Medium | {medium} | {(medium/total*100):.1f}% |
| 🔴 Hard | {hard} | {(hard/total*100):.1f}% |

### 🏆 Statistics
- **Current Streak:** {streak} days 🔥
- **Max Streak:** {max_streak} days 🏅
- **Favorite Topics:** {', '.join(progress['favorite_topics'])}

### 📝 Recent Problems
"""
    
    for problem in progress['recent_problems'][:3]:
        difficulty_emoji = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
        emoji = difficulty_emoji.get(problem['difficulty'], '⚪')
        display += f"- {emoji} **{problem['name']}** - {problem['difficulty']} ({problem['date']})\n"
    
    display += f"\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n"
    
    return display

def main():
    """Main function"""
    # Load existing progress
    progress = load_progress()
    
    # Simulate daily progress
    progress = simulate_daily_progress(progress)
    
    # Save updated progress
    save_progress(progress)
    
    # Generate display
    display = generate_progress_display(progress)
    
    # Save display content
    with open('leetcode_progress.html', 'w') as f:
        f.write(display)
    
    print(f"LeetCode progress updated: {progress['total_solved']} problems solved, {progress['current_streak']} day streak")
    return display

if __name__ == "__main__":
    main()