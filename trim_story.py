import re

# Read the extracted story
with open(r'data\test_story_man_who_would_be_king.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# The story import truncates at 24,000 chars, so let's keep ~22k
# to give the LLM good material to work with
target_chars = 22000

# Find a good cut point - try to end on a paragraph boundary
result = content[:target_chars]
# Find the last paragraph break
last_break = result.rfind('\n\n')
if last_break > target_chars - 2000:
    result = result[:last_break]

with open(r'data\test_story_man_who_would_be_king.txt', 'w', encoding='utf-8') as f:
    f.write(result)

print(f'Truncated to: {len(result)} characters')
print(f'First 200 chars:')
print(result[:200])
print(f'...')
print(f'Last 200 chars:')
print(result[-200:])
