#!/usr/bin/env python3
"""
Quick verification that all components are properly integrated.
"""

import sys
import py_compile

# Check Python syntax
files_to_check = [
    'app/services/explainability.py',
    'app/services/gemini.py',
    'app/schemas.py'
]

print("="*60)
print("SYNTAX VERIFICATION")
print("="*60)

all_ok = True
for filepath in files_to_check:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"✓ {filepath}")
    except py_compile.PyCompileError as e:
        print(f"✗ {filepath}: {e}")
        all_ok = False

if not all_ok:
    print("\n✗ SYNTAX ERRORS FOUND")
    sys.exit(1)

print("\n" + "="*60)
print("IMPORT VERIFICATION")
print("="*60)

try:
    from app.services import explainability
    print("✓ explainability module imports")
    
    from app.services.gemini import GroqTravelService
    print("✓ GroqTravelService imports")
    
    from app.schemas import ExplainabilityResponse, CostExplanation
    print("✓ Explainability schemas import")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("FUNCTION SIGNATURE VERIFICATION")
print("="*60)

# Verify key functions exist and have correct signatures
functions_to_check = [
    ('explainability', 'get_accommodation_alternatives'),
    ('explainability', 'get_transport_alternatives'),
    ('explainability', 'calculate_budget_reconciliation'),
    ('explainability', 'build_accommodation_explanation'),
    ('explainability', 'build_transport_explanation'),
    ('explainability', 'build_food_explanation'),
    ('explainability', 'build_activities_explanation'),
    ('explainability', 'build_contingency_explanation'),
    ('explainability', 'assemble_cost_explanations'),
]

for module_name, func_name in functions_to_check:
    try:
        module = sys.modules[f'app.services.{module_name}']
        func = getattr(module, func_name)
        print(f"✓ {module_name}.{func_name}")
    except (KeyError, AttributeError) as e:
        print(f"✗ {module_name}.{func_name}: {e}")
        all_ok = False

print("\n" + "="*60)
print("SCHEMA VERIFICATION")
print("="*60)

try:
    from app.schemas import (
        CostExplanation,
        FinancialSummary,
        TripMetadata,
        ExplainabilityResponse
    )
    
    # Try to instantiate a simple example
    summary = FinancialSummary(
        total_budget=50000.0,
        total_estimated_cost=48000.0,
        remaining_budget=2000.0,
        contingency_included=True,
        contingency_amount=3840.0,
        contingency_percentage=8.0
    )
    print("✓ FinancialSummary schema")
    
    exp = CostExplanation(
        category="Accommodation",
        selected_option="Mid-Range",
        selected_cost=15000.0,
        estimated_cost=15000.0,
        allocation_percentage=30.0,
        decision_factors=["Comfort: 60/100"],
        explanation="Test"
    )
    print("✓ CostExplanation schema")
    
except Exception as e:
    print(f"✗ Schema error: {e}")
    all_ok = False

print("\n" + "="*60)
if all_ok:
    print("✓ ALL VERIFICATIONS PASSED")
    print("="*60)
    sys.exit(0)
else:
    print("✗ SOME VERIFICATIONS FAILED")
    print("="*60)
    sys.exit(1)
