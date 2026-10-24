"""
Fix CompareDestinations.tsx - more careful replacement
"""

import re

# Read the file
with open('src/pages/CompareDestinations.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken option tag specifically
content = content.replace(
    '<option value=—>"" Choose Destination ""</option>',
    '<option value="">— Choose Destination —</option>'
)

# Fix any other display text that should use em dash
# But only in display context (after >), not in attributes
# Replace pattern: >""< with >—<
content = re.sub(r'>("")<', r'>—<', content)

# Fix trailing display-only empty quotes at end of ternary
# Pattern: : '—'} but should be just empty string value
content = content.replace(": '—'}", ": '—'}")

# Write back
with open('src/pages/CompareDestinations.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed CompareDestinations.tsx:")
print("  - Fixed option value attribute")
print("  - Kept em dashes only for display text")
