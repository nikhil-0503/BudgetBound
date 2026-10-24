"""
Fix CompareDestinations.tsx encoding and score display issues
"""

import re

# Read the file
with open('src/pages/CompareDestinations.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace corrupted arrow characters with proper Unicode
content = content.replace('â†³', '↳')

# Fix 2: Replace empty quote marks with em dash
content = content.replace('""', '—')

# Fix 3: Fix score displays (multiply by 100 for percentages)
# Find patterns like: plans[idx].breakdown.budget_compatibility}%
score_patterns = [
    (r'plans\[idx\]\.breakdown\.budget_compatibility\}%',
     'Math.round(plans[idx].breakdown.budget_compatibility * 100)}%'),
    (r'plans\[idx\]\.breakdown\.trip_type_match\}%',
     'Math.round(plans[idx].breakdown.trip_type_match * 100)}%'),
    (r'plans\[idx\]\.breakdown\.comfort_match\}%',
     'Math.round(plans[idx].breakdown.comfort_match * 100)}%'),
    (r'plans\[idx\]\.breakdown\.duration_suitability\}%',
     'Math.round(plans[idx].breakdown.duration_suitability * 100)}%'),
]

for pattern, replacement in score_patterns:
    content = re.sub(pattern, replacement, content)

# Fix 4: Fix value_score display (already 0-100, just needs to be rounded)
content = re.sub(
    r'plans\[idx\]\.value_score\.toFixed\(1\)',
    'Math.round(plans[idx].value_score)',
    content
)

# Write back
with open('src/pages/CompareDestinations.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed CompareDestinations.tsx:")
print("  - Replaced corrupted arrow characters (â†³ → ↳)")
print("  - Replaced empty quote marks ("" → —)")
print("  - Fixed score display formatting (0.9 → 90%)")
print("  - Rounded value_score display")
