#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("GITHUB_USERNAME", "devrajsinghal35")
OUTPUT_FILE = "assets/cyber-contributions.svg"

if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN not found. Generating a mock structure for local preview.")

def fetch_contributions(username, token):
    if not token:
        import random
        weeks = []
        for w in range(53):
            days = []
            for d in range(7):
                count = random.choice([0, 0, 0, 1, 2, 5, 10])
                level = 'NONE'
                if count > 0:
                    level = random.choice(['FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'])
                days.append({
                    "contributionCount": count,
                    "date": "2026-01-01",
                    "contributionLevel": level
                })
            weeks.append({"contributionDays": days})
        return weeks

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'login': username}}).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'errors' in result:
                print(f"GraphQL Error: {result['errors']}")
                sys.exit(1)
            return result['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        sys.exit(1)

def map_level_to_color(level):
    cyber_colors = {
        'NONE': '#050a0a',
        'FIRST_QUARTILE': '#004d16',
        'SECOND_QUARTILE': '#00802b',
        'THIRD_QUARTILE': '#00b33c',
        'FOURTH_QUARTILE': '#00ff41'
    }
    return cyber_colors.get(level, '#050a0a')

def map_level_to_opacity(level):
    op = {
        'NONE': 0.1,
        'FIRST_QUARTILE': 0.5,
        'SECOND_QUARTILE': 0.7,
        'THIRD_QUARTILE': 0.9,
        'FOURTH_QUARTILE': 1.0
    }
    return op.get(level, 0.1)

def generate_svg(weeks):
    cell_size = 14
    cell_gap = 4
    grid_w = len(weeks) * (cell_size + cell_gap)
    grid_h = 7 * (cell_size + cell_gap)
    
    total_w = grid_w + 100
    total_h = grid_h + 120
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" font-family="monospace">')
    
    # Background and Styles
    svg.append("""
    <defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="strong-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <linearGradient id="scanGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#00ff41" stop-opacity="0" />
            <stop offset="80%" stop-color="#00ff41" stop-opacity="0.1" />
            <stop offset="100%" stop-color="#00ff41" stop-opacity="0.8" />
        </linearGradient>
        <style>
            .text-title { fill: #00ff41; font-size: 16px; font-weight: bold; letter-spacing: 2px; }
            .text-sub { fill: #00802b; font-size: 12px; letter-spacing: 1px; }
            .cell { stroke: #00ff41; stroke-width: 0.5; }
        </style>
    </defs>
    <rect width="100%" height="100%" fill="#020404" />
    <rect width="100%" height="100%" fill="none" stroke="#004d16" stroke-width="2" />
    """)

    # Grid Pattern Background Overlay
    svg.append(f'<rect width="100%" height="100%" fill="none" stroke="#001a05" stroke-width="1" stroke-dasharray="2,2" />')

    # Headers
    svg.append(f'<text x="50" y="40" class="text-title">CYBERCOM // COMMIT INTELLIGENCE RADAR</text>')
    svg.append(f'<text x="50" y="58" class="text-sub">TARGET: DEVRAJ SINGHAL | STATUS: ACTIVE MONITORING</text>')

    offset_x = 50
    offset_y = 80
    
    # Group for the cells
    svg.append('<g>')
    
    for x_idx, week in enumerate(weeks):
        for y_idx, day in enumerate(week.get('contributionDays', [])):
            level = day['contributionLevel']
            px = offset_x + x_idx * (cell_size + cell_gap)
            py = offset_y + y_idx * (cell_size + cell_gap)
            
            color = map_level_to_color(level)
            opacity = map_level_to_opacity(level)
            
            is_active = level != 'NONE'
            filter_attr = 'filter="url(#glow)"' if level in ['THIRD_QUARTILE', 'FOURTH_QUARTILE'] else ''
            
            # Animate the active cells to flicker like digital data
            if is_active:
                dur = 2.0 + (x_idx % 5) * 0.5
                svg.append(f'''
                <rect x="{px}" y="{py}" width="{cell_size}" height="{cell_size}" fill="{color}" opacity="{opacity}" class="cell" {filter_attr} rx="2" ry="2">
                    <animate attributeName="opacity" values="{opacity};{opacity*0.5};{opacity};{opacity}" keyTimes="0;0.1;0.2;1" dur="{dur}s" repeatCount="indefinite" />
                </rect>
                ''')
            else:
                svg.append(f'<rect x="{px}" y="{py}" width="{cell_size}" height="{cell_size}" fill="#050a0a" stroke="#001a05" stroke-width="1" opacity="0.3" rx="2" ry="2" />')
                
    svg.append('</g>')

    # Animated Scanner
    # Moves across the grid from left to right over 4 seconds
    svg.append(f'''
    <rect y="{offset_y - 10}" width="40" height="{grid_h + 20}" fill="url(#scanGradient)">
        <animate attributeName="x" from="{offset_x - 40}" to="{offset_x + grid_w}" dur="4s" repeatCount="indefinite" />
    </rect>
    ''')
    
    # Scanner line
    svg.append(f'''
    <line y1="{offset_y - 10}" y2="{offset_y + grid_h + 10}" stroke="#00ff41" stroke-width="2" filter="url(#glow)">
        <animate attributeName="x1" from="{offset_x}" to="{offset_x + grid_w + 40}" dur="4s" repeatCount="indefinite" />
        <animate attributeName="x2" from="{offset_x}" to="{offset_x + grid_w + 40}" dur="4s" repeatCount="indefinite" />
    </line>
    ''')

    # Legend
    legend_y = total_h - 25
    svg.append(f'<text x="50" y="{legend_y + 4}" class="text-sub">SYSTEM IDLE</text>')
    
    svg.append(f'<rect x="140" y="{legend_y - 5}" width="{cell_size}" height="{cell_size}" fill="#050a0a" stroke="#001a05" />')
    svg.append(f'<rect x="158" y="{legend_y - 5}" width="{cell_size}" height="{cell_size}" fill="#004d16" />')
    svg.append(f'<rect x="176" y="{legend_y - 5}" width="{cell_size}" height="{cell_size}" fill="#00802b" />')
    svg.append(f'<rect x="194" y="{legend_y - 5}" width="{cell_size}" height="{cell_size}" fill="#00b33c" filter="url(#glow)" />')
    svg.append(f'<rect x="212" y="{legend_y - 5}" width="{cell_size}" height="{cell_size}" fill="#00ff41" filter="url(#strong-glow)" />')
    
    svg.append(f'<text x="235" y="{legend_y + 4}" class="text-sub">HEAVY BREACH DETECTED</text>')

    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(svg))
    
    print(f"Successfully generated {OUTPUT_FILE}")

def main():
    weeks = fetch_contributions(USERNAME, GITHUB_TOKEN)
    generate_svg(weeks)

if __name__ == "__main__":
    main()
