#!/usr/bin/env python3
"""CECS 427 - Matching Markets assignment.

Usage:
    python3 markets.py market GRAPH.gml OUTPUT.png
    python3 markets.py intermediary GRAPH.gml OUTPUT.png

---------------------------------------------------------------------------
Generative AI Disclosure (Syllabus Section 16)
---------------------------------------------------------------------------
The following generative AI tools were used in this assignment:
    Cursor IDE agent (Claude)

Usage of AI:
    - Used AI to map the lecture slides (Prices and Payoffs, Preferred
      Sellers, Market-Clearing Prices, Perfect Matching; Trading Network,
      Bid/Ask Prices and Payoffs) to the required output fields and plan
      the program layout.
---------------------------------------------------------------------------
"""

import math
import os
import sys

import matplotlib.pyplot as plt
import networkx as nx

plt.switch_backend("Agg")


def fail(message):
    """Print an error to stderr and exit with a nonzero status."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_graph(path):
    """Read a graph from a GML file (node names are normalized to strings)."""
    if not os.path.isfile(path):
        fail(f"file not found: {path}")
    try:
        G = nx.read_gml(path)
    except Exception as exc:
        fail(f"could not read GML file {path}: {exc}")
    if G.is_multigraph():
        fail("graph must not contain parallel edges")
    return nx.relabel_nodes(G, str)


def number(data, attr, where):
    """Return data[attr] as a finite float, or exit if missing/non-numeric."""
    if attr not in data:
        fail(f"{where} is missing required attribute '{attr}'")
    try:
        value = float(data[attr])
    except (TypeError, ValueError):
        fail(f"{where} has non-numeric '{attr}': {data[attr]!r}")
    if not math.isfinite(value):
        fail(f"{where} has non-finite '{attr}': {data[attr]!r}")
    return value


def fmt3(x):
    return f"{float(x):.3f}"


def new_figure():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis("off")
    return fig, ax


def finish(lines, fig, output):
    """Save the PNG, then print the result lines and GRAPH_IMAGE."""
    try:
        fig.savefig(output, format="png", bbox_inches="tight")
    except Exception as exc:
        fail(f"could not write image {output}: {exc}")
    plt.close(fig)
    for line in lines:
        print(line)
    print(f"GRAPH_IMAGE {output}")


def node_type(data):
    return str(data.get("type", "")).lower()


def valuation_of(G, buyer, seller):
    """Valuation on the (undirected) buyer-seller edge."""
    return float(G.edges[buyer, seller]["valuation"])


# ---------------------------------------------------------------------------
# market
# ---------------------------------------------------------------------------

def parse_market_graph(G):
    """Validate the bipartite market; return (buyers, sellers, undirected G)."""
    G = G.to_undirected()

    buyers, sellers = [], []
    for n, data in G.nodes(data=True):
        t = node_type(data)
        if t == "buyer":
            buyers.append(n)
        elif t == "seller":
            number(data, "price", f"seller {n}")
            sellers.append(n)
        else:
            fail(f"node {n} has invalid type '{data.get('type')}' for market graph")

    buyers = sorted(buyers)
    sellers = sorted(sellers)
    if not buyers or not sellers:
        fail("market graph must contain at least one buyer and one seller")

    seller_set, buyer_set = set(sellers), set(buyers)
    for u, v, data in G.edges(data=True):
        if not ({u, v} & buyer_set and {u, v} & seller_set):
            fail(f"edge {u}-{v} is not a buyer-seller edge")
        number(data, "valuation", f"edge {u}-{v}")

    return buyers, sellers, G


def preferred_sellers(G, buyers, sellers):
    """Map each buyer to their preferred seller list (alphabetical)."""
    preferred = {}
    for buyer in buyers:
        best = None
        choices = []
        for seller in sellers:
            if not G.has_edge(buyer, seller):
                continue
            payoff = valuation_of(G, buyer, seller) - float(G.nodes[seller]["price"])
            if payoff < 0:
                continue
            if best is None or payoff > best:
                best = payoff
                choices = [seller]
            elif payoff == best:
                choices.append(seller)
        preferred[buyer] = sorted(choices)
    return preferred


def maximum_matching(buyers, preferred):
    """Maximum matching in the preferred-seller graph via augmenting paths.

    Buyers and their preferred sellers are visited in alphabetical order, so
    the same maximum matching is returned on every run.
    """
    seller_owner = {}

    def augment(buyer, seen):
        for seller in preferred[buyer]:
            if seller in seen:
                continue
            seen.add(seller)
            if seller not in seller_owner or augment(seller_owner[seller], seen):
                seller_owner[seller] = buyer
                return True
        return False

    for buyer in buyers:
        augment(buyer, set())

    owner_to_seller = {b: s for s, b in seller_owner.items()}
    return [(b, owner_to_seller[b]) for b in buyers if b in owner_to_seller]


def draw_market(G, buyers, sellers, preferred, output_title):
    fig, ax = new_figure()
    pos = {}
    for i, b in enumerate(buyers):
        pos[b] = (0.0, 1.0 - (i / max(len(buyers) - 1, 1)))
    for i, s in enumerate(sellers):
        pos[s] = (1.0, 1.0 - (i / max(len(sellers) - 1, 1)))

    preferred_set = {(b, s) for b, prefs in preferred.items() for s in prefs}
    preferred_set |= {(s, b) for b, s in preferred_set}

    other_edges = []
    preferred_edges = []
    for u, v in G.edges():
        if (u, v) in preferred_set or (v, u) in preferred_set:
            preferred_edges.append((u, v))
        else:
            other_edges.append((u, v))

    nx.draw_networkx_nodes(
        G, pos, ax=ax, nodelist=buyers, node_color="lightblue",
        node_size=900, label="buyers",
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax, nodelist=sellers, node_color="lightgreen",
        node_size=900, label="sellers",
    )

    labels = {b: str(b) for b in buyers}
    labels.update({s: f"{s}\np={float(G.nodes[s]['price']):g}" for s in sellers})
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=9)

    if other_edges:
        nx.draw_networkx_edges(
            G, pos, ax=ax, edgelist=other_edges,
            edge_color="gray", width=1.2, alpha=0.7,
        )
    if preferred_edges:
        nx.draw_networkx_edges(
            G, pos, ax=ax, edgelist=preferred_edges,
            edge_color="red", width=2.0,
        )

    edge_labels = {
        (u, v): f"{float(data['valuation']):g}" for u, v, data in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=8)

    ax.set_title(output_title)
    ax.legend(scatterpoints=1, markerscale=0.5, loc="upper center")
    ax.margins(0.15)
    return fig


def cmd_market(args):
    path, output = args
    buyers, sellers, G = parse_market_graph(load_graph(path))
    preferred = preferred_sellers(G, buyers, sellers)
    matching = maximum_matching(buyers, preferred)

    matched_buyers = {b for b, _ in matching}
    matched_sellers = {s for _, s in matching}
    clearing = (
        len(matched_buyers) == len(buyers)
        and len(matched_sellers) == len(sellers)
    )

    total_val = sum(valuation_of(G, b, s) for b, s in matching)

    pref_tokens = [f"{b}:{','.join(preferred[b])}" for b in buyers]

    match_tokens = [f"{b}-{s}" for b, s in matching]

    lines = [
        f"BUYERS {len(buyers)}",
        f"SELLERS {len(sellers)}",
        " ".join(["PREFERRED"] + pref_tokens),
        f"MATCHING_SIZE {len(matching)}",
        f"MARKET_CLEARING {'YES' if clearing else 'NO'}",
        " ".join(["MATCHING"] + match_tokens),
        f"TOTAL_VALUATION {fmt3(total_val)}",
    ]

    fig = draw_market(
        G, buyers, sellers, preferred,
        "Matching Market: Preferred Sellers",
    )
    finish(lines, fig, output)


# ---------------------------------------------------------------------------
# intermediary
# ---------------------------------------------------------------------------

def parse_intermediary_graph(G):
    """Validate the trading network.

    Returns (sellers, traders, buyers, D) where D is a directed graph with
    every edge oriented seller->trader (bid) or trader->buyer (ask), whether
    or not the GML itself was declared directed.
    """
    sellers, traders, buyers = [], [], []
    D = nx.DiGraph()
    for n, data in G.nodes(data=True):
        t = node_type(data)
        if t == "seller":
            sellers.append(n)
        elif t == "trader":
            traders.append(n)
        elif t == "buyer":
            number(data, "value", f"buyer {n}")
            buyers.append(n)
        else:
            fail(
                f"node {n} has invalid type '{data.get('type')}' "
                "for intermediary graph"
            )
        D.add_node(n, **data)

    sellers = sorted(sellers)
    traders = sorted(traders)
    buyers = sorted(buyers)
    if not sellers or not traders or not buyers:
        fail("intermediary graph needs sellers, traders, and buyers")

    seller_set, trader_set, buyer_set = set(sellers), set(traders), set(buyers)
    for u, v, data in G.edges(data=True):
        where = f"edge {u}-{v}"
        pairs = [(u, v)] if G.is_directed() else [(u, v), (v, u)]
        for a, b in pairs:
            if a in seller_set and b in trader_set:
                number(data, "bid", where)
                D.add_edge(a, b, **data)
                break
            if a in trader_set and b in buyer_set:
                number(data, "ask", where)
                D.add_edge(a, b, **data)
                break
        else:
            fail(f"{where} is not a valid seller->trader or trader->buyer edge")

    return sellers, traders, buyers, D


def seller_choices(G, sellers):
    """seller -> (trader, bid); always chooses max bid, alphabetical tie-break."""
    choices = {}
    for seller in sellers:
        best_bid = None
        best_trader = None
        for _, trader, data in G.out_edges(seller, data=True):
            bid = float(data["bid"])
            if (
                best_bid is None
                or bid > best_bid
                or (bid == best_bid and trader < best_trader)
            ):
                best_bid = bid
                best_trader = trader
        if best_trader is None:
            fail(f"seller {seller} has no bid edges to traders")
        choices[seller] = (best_trader, best_bid)
    return choices


def buyer_choices(G, buyers):
    """buyer -> (trader, ask) or None if no acceptable ask."""
    choices = {}
    for buyer in buyers:
        value = float(G.nodes[buyer]["value"])
        best_ask = None
        best_trader = None
        for trader, _, data in G.in_edges(buyer, data=True):
            ask = float(data["ask"])
            if ask > value:
                continue
            if (
                best_ask is None
                or ask < best_ask
                or (ask == best_ask and trader < best_trader)
            ):
                best_ask = ask
                best_trader = trader
        if best_trader is None:
            choices[buyer] = None
        else:
            choices[buyer] = (best_trader, best_ask)
    return choices


def trader_payoffs(traders, s_choices, b_choices):
    payoffs = {t: 0.0 for t in traders}
    for trader, bid in s_choices.values():
        payoffs[trader] -= bid
    for choice in b_choices.values():
        if choice is not None:
            trader, ask = choice
            payoffs[trader] += ask
    return payoffs


def draw_intermediary(G, sellers, traders, buyers, s_choices, b_choices):
    fig, ax = new_figure()
    pos = {}
    for i, s in enumerate(sellers):
        pos[s] = (0.0, 1.0 - (i / max(len(sellers) - 1, 1)))
    for i, t in enumerate(traders):
        pos[t] = (0.5, 1.0 - (i / max(len(traders) - 1, 1)))
    for i, b in enumerate(buyers):
        pos[b] = (1.0, 1.0 - (i / max(len(buyers) - 1, 1)))

    accepted = {(s, t) for s, (t, _) in s_choices.items()}
    accepted |= {(c[0], b) for b, c in b_choices.items() if c is not None}

    other = [e for e in G.edges() if e not in accepted]
    accepted_list = [e for e in G.edges() if e in accepted]

    nx.draw_networkx_nodes(
        G, pos, ax=ax, nodelist=sellers, node_color="lightgreen",
        node_size=900, label="sellers",
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax, nodelist=traders, node_color="orange",
        node_size=900, label="traders",
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax, nodelist=buyers, node_color="lightblue",
        node_size=900, label="buyers",
    )
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9)

    if other:
        nx.draw_networkx_edges(
            G, pos, ax=ax, edgelist=other, edge_color="gray",
            width=1.2, alpha=0.7, arrows=True, arrowsize=15,
            connectionstyle="arc3,rad=0.05",
        )
    if accepted_list:
        nx.draw_networkx_edges(
            G, pos, ax=ax, edgelist=accepted_list, edge_color="red",
            width=2.0, arrows=True, arrowsize=15,
            connectionstyle="arc3,rad=0.05",
        )

    edge_labels = {}
    for u, v, data in G.edges(data=True):
        if "bid" in data:
            edge_labels[(u, v)] = f"bid={float(data['bid']):g}"
        elif "ask" in data:
            edge_labels[(u, v)] = f"ask={float(data['ask']):g}"
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax, font_size=7,
    )

    ax.set_title("Trading Network: Accepted Bids and Asks")
    ax.legend(scatterpoints=1, markerscale=0.5, loc="upper center")
    ax.margins(0.15)
    return fig


def cmd_intermediary(args):
    path, output = args
    sellers, traders, buyers, G = parse_intermediary_graph(load_graph(path))
    s_choices = seller_choices(G, sellers)
    b_choices = buyer_choices(G, buyers)
    payoffs = trader_payoffs(traders, s_choices, b_choices)

    seller_tokens = [
        f"{s}:{s_choices[s][0]}@{fmt3(s_choices[s][1])}" for s in sellers
    ]
    buyer_tokens = [
        f"{b}:NONE" if b_choices[b] is None
        else f"{b}:{b_choices[b][0]}@{fmt3(b_choices[b][1])}"
        for b in buyers
    ]

    payoff_tokens = [f"{t}:{fmt3(payoffs[t])}" for t in traders]
    total = sum(payoffs.values())

    lines = [
        f"SELLERS {len(sellers)}",
        f"TRADERS {len(traders)}",
        f"BUYERS {len(buyers)}",
        " ".join(["SELLER_CHOICES"] + seller_tokens),
        " ".join(["BUYER_CHOICES"] + buyer_tokens),
        " ".join(["TRADER_PAYOFFS"] + payoff_tokens),
        f"TOTAL_TRADER_PAYOFF {fmt3(total)}",
    ]

    fig = draw_intermediary(G, sellers, traders, buyers, s_choices, b_choices)
    finish(lines, fig, output)


COMMANDS = {
    "market": (2, cmd_market, "GRAPH.gml OUTPUT.png"),
    "intermediary": (2, cmd_intermediary, "GRAPH.gml OUTPUT.png"),
}


def main():
    if len(sys.argv) < 2:
        fail("usage: markets.py market|intermediary ...")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        fail(f"unknown command: {command}")

    expected, handler, usage = COMMANDS[command]
    if len(args) != expected:
        fail(f"usage: markets.py {command} {usage}")

    handler(args)


if __name__ == "__main__":
    main()
