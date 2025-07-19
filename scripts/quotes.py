#!/usr/bin/env python3
"""
Random quotes and programming jokes fetcher
Fetches daily programming jokes or inspirational quotes
"""

import requests
import json
import random
from datetime import datetime

def fetch_programming_joke():
    """Fetch a programming joke from JokeAPI"""
    try:
        url = "https://v2.jokeapi.dev/joke/Programming?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['type'] == 'single':
            return data['joke']
        else:
            return f"{data['setup']}\n\n{data['delivery']}"
    except Exception as e:
        print(f"Error fetching joke: {e}")
        return None

def fetch_inspirational_quote():
    """Fetch an inspirational quote from quotable.io"""
    try:
        url = "https://api.quotable.io/random?tags=technology,motivational,success"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return f'"{data["content"]}" - {data["author"]}'
    except Exception as e:
        print(f"Error fetching quote: {e}")
        return None

def get_fallback_quotes():
    """Fallback quotes in case APIs are unavailable"""
    quotes = [
        '"The only way to do great work is to love what you do." - Steve Jobs',
        '"Innovation distinguishes between a leader and a follower." - Steve Jobs',
        '"Talk is cheap. Show me the code." - Linus Torvalds',
        '"First, solve the problem. Then, write the code." - John Johnson',
        '"Code is like humor. When you have to explain it, it\'s bad." - Cory House',
        '"Experience is the name everyone gives to their mistakes." - Oscar Wilde',
        '"In order to be irreplaceable, one must always be different." - Coco Chanel',
        '"The best time to plant a tree was 20 years ago. The second best time is now." - Chinese Proverb'
    ]
    return random.choice(quotes)

def generate_daily_content():
    """Generate daily quote or joke content"""
    # Alternating between jokes and quotes based on day
    today = datetime.now().day
    
    if today % 2 == 0:
        # Even days: Programming jokes
        content = fetch_programming_joke()
        if content:
            return f"## 😄 Daily Programming Humor\n\n{content}\n"
        else:
            return f"## 💭 Daily Quote\n\n{get_fallback_quotes()}\n"
    else:
        # Odd days: Inspirational quotes
        content = fetch_inspirational_quote()
        if content:
            return f"## 💭 Daily Inspiration\n\n{content}\n"
        else:
            return f"## 💭 Daily Quote\n\n{get_fallback_quotes()}\n"

def main():
    """Main function"""
    content = generate_daily_content()
    
    # Save to file for use in README update
    with open('daily_content.html', 'w') as f:
        f.write(content)
    
    print("Daily content generated successfully!")
    return content

if __name__ == "__main__":
    main()