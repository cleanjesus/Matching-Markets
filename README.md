# Matching Markets

CECS 427 (Network Analysis) assignment: model matching markets with bipartite graphs and trading networks with intermediaries.

## Features

| Command | What it does |
| --- | --- |
| `market` | Reads a buyer/seller graph with prices and valuations, computes each buyer's preferred sellers, finds a maximum bipartite matching, and reports whether the prices are market-clearing along with the total valuation. |
| `intermediary` | Reads a trading network (sellers, traders, buyers) with bid/ask prices, determines each seller's and buyer's best choice, and computes each trader's payoff. |

Each command prints its results to stdout and saves a PNG visualization. Invalid input exits with a nonzero status, and there are no interactive prompts.

## Requirements

- Python 3
- [NetworkX](https://networkx.org/)
- [Matplotlib](https://matplotlib.org/)

```bash
pip install networkx matplotlib
```

## Usage

```bash
python3 markets.py market GRAPH.gml OUTPUT.png
python3 markets.py intermediary GRAPH.gml OUTPUT.png
```

Examples using the included samples:

```bash
python3 markets.py market samples/market.gml market.png
python3 markets.py market samples/market_noclear.gml market_noclear.png
python3 markets.py intermediary samples/intermediary.gml intermediary.png
```

Sample output of `market`:

```
BUYERS 3
SELLERS 3
PREFERRED x:a y:b,c z:b
...
```

### Input format

Graphs are GML files. In a market graph, nodes have `type` (`seller` or `buyer`), sellers have a `price`, and buyer–seller edges have a `valuation`.

```
node [ id 0 label "a" type "seller" price 5 ]
node [ id 3 label "x" type "buyer" ]
edge [ source 3 target 0 valuation 12 ]
```

## Project Structure

| Path | Description |
| --- | --- |
| `markets.py` | Main program (`market` and `intermediary` commands) |
| `samples/` | Sample GML inputs (`market`, `market_noclear`, `intermediary`) |
| `market.png`, `intermediary.png` | Example output images |

## Generative AI Disclosure

Generative AI (Cursor IDE agent) was used to help map lecture material to the required output and plan the program layout. See the header of `markets.py` for details.
