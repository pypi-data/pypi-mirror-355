#!/usr/bin/env python3
"""
Phi Mathematics and Golden Ratio Calculations
"""

import click
import math
from . import PHI

def phi_main():
    """Phi mathematics main entry point"""
    click.echo("🌟 Phi Mathematics")
    click.echo("=" * 20)
    click.echo(f"φ = {PHI}")
    click.echo(f"φ² = {PHI**2}")
    click.echo(f"1/φ = {1/PHI}")
    click.echo(f"φ - 1/φ = {PHI - 1/PHI}")
    
    # Fibonacci sequence with phi
    click.echo("\n📊 Fibonacci & Phi:")
    fib = [0, 1]
    for i in range(2, 10):
        fib.append(fib[i-1] + fib[i-2])
    
    for i in range(1, len(fib)-1):
        ratio = fib[i+1] / fib[i] if fib[i] != 0 else 0
        click.echo(f"F({i+1})/F({i}) = {ratio:.6f}")
    
    click.echo(f"\n✨ Converges to φ = {PHI}")

@click.command()
@click.argument('n', type=int, default=1)
def calculate(n):
    """Calculate phi^n"""
    result = PHI ** n
    click.echo(f"φ^{n} = {result}")

@click.command()
@click.argument('a', type=float)
@click.argument('b', type=float)  
def golden_ratio(a, b):
    """Check if a:b is golden ratio"""
    ratio = a / b if b != 0 else float('inf')
    phi_diff = abs(ratio - PHI)
    
    click.echo(f"Ratio: {ratio:.6f}")
    click.echo(f"φ: {PHI:.6f}")
    click.echo(f"Difference: {phi_diff:.6f}")
    
    if phi_diff < 0.001:
        click.echo("✅ Golden ratio detected!")
    else:
        click.echo("❌ Not golden ratio")

if __name__ == '__main__':
    phi_main()