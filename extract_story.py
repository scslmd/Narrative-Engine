import re

with open(r'C:\Users\SLuh\.local\share\opencode\tool-output\tool_dbdb333db001spGVBlzkDXfVBA', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove HTML-like tags
content = re.sub(r'<[^>]+>', ' ', content)

# Find the story text
story_start = content.find('The Man Who Would Be King')
if story_start != -1:
    lines = content[story_start:].split('\n')
    story_text = []
    in_story = False
    for line in lines:
        stripped = line.strip()
        # Look for the subtitle line
        if 'Brother to a Prince and fellow to a beggar' in stripped:
            in_story = True
            continue
        if in_story:
            story_text.append(stripped)

    result = '\n\n'.join(story_text)
    
    # Remove excessive whitespace
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = result.strip()
    
    # Write to output
    with open(r'data\test_story_man_who_would_be_king.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f'Story saved: {len(result)} characters')
else:
    print('Story not found')
