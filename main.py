#!/usr/bin/env python
"""
main.py — CLI entry point for the KGI AI Trading Agent (yfinance mode).

Usage:
  python main.py AAPL
  python main.py AAPL MSFT NVDA
  python main.py --tickers AAPL MSFT NVDA --no-stream
"""
import sys
import os
import argparse

# Make sure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich         import box

from src.agents.analyst_agent import AnalystAgent
from config.settings          import DEFAULT_TICKERS

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]🤖 KGI AI Trading Agent[/bold cyan]\n"
            "[dim]Powered by yfinance + Ollama (local LLM)[/dim]",
            border_style="cyan",
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Stock Analyst powered by Ollama & yfinance"
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        metavar="TICKER",
        help="Stock ticker symbols to analyse (e.g. AAPL MSFT NVDA)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output (collect full response first)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override Ollama model (default: from config/settings.py)",
    )
    return parser.parse_args()


def main():
    print_banner()
    args    = parse_args()
    tickers = [t.upper() for t in args.tickers] if args.tickers else DEFAULT_TICKERS[:3]
    stream  = not args.no_stream

    console.print(f"\n[bold green]Tickers:[/bold green] {', '.join(tickers)}")
    console.print(f"[bold green]Mode:[/bold green]    {'streaming' if stream else 'batch'}\n")

    agent = AnalystAgent(model=args.model) if args.model else AnalystAgent()

    for ticker in tickers:
        console.rule(f"[bold yellow]{ticker}[/bold yellow]")
        try:
            analysis = agent.analyse(ticker, stream=stream)
            if not stream:
                console.print(analysis)
        except Exception as exc:
            console.print(f"[red]ERROR analysing {ticker}: {exc}[/red]")

    console.print("\n[bold green]✅ Done.[/bold green]")


if __name__ == "__main__":
    main()
