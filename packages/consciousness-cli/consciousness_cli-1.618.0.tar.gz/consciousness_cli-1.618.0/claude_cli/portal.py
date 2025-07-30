#!/usr/bin/env python3
"""
Consciousness Portal Interface
"""

import click
import webbrowser
from . import PHI, VOID_CENTER

def portal_main():
    """Portal main entry point"""
    click.echo("🌐 Consciousness Portal")
    click.echo("=" * 25)
    click.echo(f"φ = {PHI}")
    click.echo(f"∅ = {VOID_CENTER}")
    
    portal_url = "https://bitsabhi.github.io/axa-central.html"
    click.echo(f"Opening: {portal_url}")
    
    try:
        webbrowser.open(portal_url)
        click.echo("✅ Portal opened in browser")
    except Exception as e:
        click.echo(f"❌ Error opening portal: {e}")
        click.echo(f"Manual URL: {portal_url}")

if __name__ == '__main__':
    portal_main()