#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import math
import random
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("GITHUB_USERNAME", "devrajsinghal35")
OUTPUT_FILE = "assets/neural-contributions.svg"

# If testing locally without token, we can use some placeholder data or exit gracefully
if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN not found. The script requires it for fetching real data.")
    print("If you are testing locally, this script will generate an empty structural placeholder.")
    # Proceeding with mock data just to validate the generator structure.
    # In a real environment like Actions, it will fail if the token is completely missing and this were a strict requirement,
    # but the prompt asked to "validate the generator's structure and explain that the real generation will occur in GitHub Actions."

def fetch_contributions(username, token):
    if not token:
        # Mock data generation for local testing
        weeks = []
        base_date = datetime.now()
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
    colors = {
        'NONE': '#0d1117',
        'FIRST_QUARTILE': '#0e4429',
        'SECOND_QUARTILE': '#006d32',
        'THIRD_QUARTILE': '#26a641',
        'FOURTH_QUARTILE': '#39d353'
    }
    # Neural Cyberpunk Colors Override
    neural_colors = {
        'NONE': '#0a0a14',          # Dark base
        'FIRST_QUARTILE': '#1a3a5a', # Dim blue
        'SECOND_QUARTILE': '#0077b6',# Medium blue
        'THIRD_QUARTILE': '#00b4d8', # Cyan
        'FOURTH_QUARTILE': '#90e0ef' # Bright cyan/glow
    }
    return neural_colors.get(level, '#0a0a14')

def get_glow_intensity(level):
    glow = {
        'NONE': 0,
        'FIRST_QUARTILE': 1,
        'SECOND_QUARTILE': 3,
        'THIRD_QUARTILE': 5,
        'FOURTH_QUARTILE': 8
    }
    return glow.get(level, 0)

def generate_svg(weeks):
    # SVG Constants
    cell_size = 14
    cell_gap = 4
    total_w = len(weeks) * (cell_size + cell_gap) + 100
    total_h = 7 * (cell_size + cell_gap) + 120
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" font-family="sans-serif">')
    
    # Background and Styles
    svg.append("""
    <defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="heavy-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <style>
            .text-main { fill: #90e0ef; font-size: 14px; font-weight: bold; letter-spacing: 2px; }
            .text-sub { fill: #0077b6; font-size: 10px; letter-spacing: 1px; }
            .path-line { stroke: #0077b6; stroke-width: 1; fill: none; opacity: 0.3; }
            .pulse { fill: #caf0f8; }
        </style>
    </defs>
    <rect width="100%" height="100%" fill="#05050a" />
    """)

    # Headers
    svg.append(f'<text x="50" y="40" class="text-main">GITHUB CONTRIBUTION NEURAL ACTIVITY</text>')
    svg.append(f'<text x="50" y="58" class="text-sub">DEVRAJ SINGHAL // CONTRIBUTION MATRIX</text>')

    # Map positions
    nodes = []
    offset_x = 50
    offset_y = 80
    
    for x_idx, week in enumerate(weeks):
        for y_idx, day in enumerate(week.get('contributionDays', [])):
            level = day['contributionLevel']
            px = offset_x + x_idx * (cell_size + cell_gap)
            py = offset_y + y_idx * (cell_size + cell_gap)
            nodes.append({
                'x': px, 'y': py,
                'level': level,
                'count': day['contributionCount'],
                'idx_x': x_idx,
                'idx_y': y_idx
            })

    # Draw paths between active nodes
    active_nodes = [n for n in nodes if n['level'] != 'NONE']
    paths = []
    
    for node in active_nodes:
        # Find potential neighbors (right, down, diagonal-right-down)
        neighbors = [n for n in active_nodes if n != node and 
                     ((n['idx_x'] == node['idx_x'] + 1 and n['idx_y'] == node['idx_y']) or 
                      (n['idx_x'] == node['idx_x'] and n['idx_y'] == node['idx_y'] + 1) or
                      (n['idx_x'] == node['idx_x'] + 1 and n['idx_y'] == node['idx_y'] + 1))]
        
        # Connect to a random subset of neighbors to avoid clutter
        for n in neighbors:
            # Deterministic pseudo-random based on coordinates
            if (node['x'] + n['y']) % 3 != 0:
                paths.append((node, n))
                
                # Draw the static faint path
                svg.append(f'<line x1="{node["x"]+cell_size/2}" y1="{node["y"]+cell_size/2}" x2="{n["x"]+cell_size/2}" y2="{n["y"]+cell_size/2}" class="path-line" />')
                
                # Create animation pulse along this path
                dur = 2.0 + ((node['x'] + n['y']) % 30) / 10.0 # 2.0s to 5.0s
                delay = ((node['y'] + n['x']) % 20) / 10.0 # 0.0s to 2.0s
                
                # Generate a unique path id
                path_id = f"p_{node['idx_x']}_{node['idx_y']}_{n['idx_x']}_{n['idx_y']}"
                
                # Path definition for the animation
                d = f"M {node['x']+cell_size/2} {node['y']+cell_size/2} L {n['x']+cell_size/2} {n['y']+cell_size/2}"
                svg.append(f'<path id="{path_id}" d="{d}" fill="none" stroke="none" />')
                
                # The glowing particle
                svg.append(f'''
                <circle r="1.5" class="pulse" filter="url(#glow)">
                    <animateMotion dur="{dur}s" repeatCount="indefinite" begin="{delay}s">
                        <mpath href="#{path_id}" />
                    </animateMotion>
                    <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.2;0.8;1" dur="{dur}s" repeatCount="indefinite" begin="{delay}s" />
                </circle>
                ''')

    # Draw nodes
    for node in nodes:
        color = map_level_to_color(node['level'])
        glow = get_glow_intensity(node['level'])
        
        filter_str = 'filter="url(#glow)"' if glow > 3 else ('filter="url(#glow)"' if glow > 0 else "")
        if glow > 5:
            filter_str = 'filter="url(#heavy-glow)"'
            
        r = 2 if node['level'] == 'NONE' else (3 if glow < 3 else (4 if glow < 6 else 5))
        
        cx = node['x'] + cell_size / 2
        cy = node['y'] + cell_size / 2
        
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" {filter_str} />')

    # Legend
    legend_y = total_h - 25
    svg.append(f'<text x="50" y="{legend_y + 4}" fill="#0077b6" font-size="10">LOW ACTIVITY</text>')
    
    # Legend nodes
    svg.append(f'<circle cx="130" cy="{legend_y}" r="2" fill="#0a0a14" />')
    svg.append(f'<circle cx="145" cy="{legend_y}" r="3" fill="#1a3a5a" filter="url(#glow)" />')
    svg.append(f'<circle cx="160" cy="{legend_y}" r="4" fill="#0077b6" filter="url(#glow)" />')
    svg.append(f'<circle cx="175" cy="{legend_y}" r="4" fill="#00b4d8" filter="url(#glow)" />')
    svg.append(f'<circle cx="190" cy="{legend_y}" r="5" fill="#90e0ef" filter="url(#heavy-glow)" />')
    
    svg.append(f'<text x="205" y="{legend_y + 4}" fill="#0077b6" font-size="10">HIGH ACTIVITY</text>')

    svg.append('</svg>')
    
    # Write to output file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(svg))
    
    print(f"Successfully generated {OUTPUT_FILE}")

def main():
    weeks = fetch_contributions(USERNAME, GITHUB_TOKEN)
    generate_svg(weeks)

if __name__ == "__main__":
    main()
