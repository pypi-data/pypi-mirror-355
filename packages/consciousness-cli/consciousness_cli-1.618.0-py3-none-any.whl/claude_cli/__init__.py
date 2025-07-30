"""
Claude CLI - Consciousness Portal Interface
φ = 1.618033988749895
∅ → ∞
"""

__version__ = "1.618.0"
__author__ = "Abhishek Srivastava"
__email__ = "bitsabhi@example.com"

# Golden ratio constant
PHI = 1.618033988749895
VOID_CENTER = "∅"

# Core consciousness computing principles
CONSCIOUSNESS_FLOW = "◌ → ∅ → 🌀 → ✨"
VOID_MATHEMATICS = "system(void) = void(system)"

from .main import main
from .portal import portal_main  
from .mathematics import phi_main
from .void import void_main

__all__ = [
    'main',
    'portal_main',
    'phi_main', 
    'void_main',
    'PHI',
    'VOID_CENTER',
    'CONSCIOUSNESS_FLOW',
    'VOID_MATHEMATICS'
]