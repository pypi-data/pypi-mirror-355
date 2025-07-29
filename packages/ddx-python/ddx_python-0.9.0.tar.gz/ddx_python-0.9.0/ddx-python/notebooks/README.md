# ddx-python-notebooks

A curated collection of Jupyter notebooks for exploring on-chain state, performance metrics, and frontend analytics via the `ddx-python` client.

## Prerequisites

- Python 3.10+  
- A local checkout of `ddx-python` (sibling directory)  
- JupyterLab or Jupyter Notebook

## Installation

From this `notebooks/` folder:

```bash
# installs notebook deps and links in the local ddx-python package
python3 -m pip install -e .
```

## Launch

```bash
jupyter lab
# or
jupyter notebook
```

Open any `.ipynb` from the list below.

## Available Notebooks

- **auditor_replay.ipynb**  
  Replay & validate SMT-based state transitions.  
- **performance_dashboard.ipynb**  
  Visualize throughput, latency, and resource metrics.  
- **exchange_dashboard.ipynb**  
  Inspect trade history and on-chain order-book snapshots.  
- **frontend_dashboard.ipynb**  
  Analyze user‐level metrics: positions, PnL, fees.  
- **multi_node_diverge.ipynb**  
  Detect state divergences across node instances.  
- **state_root_mismatch.ipynb**  
  Debug mismatched state roots in forked/lagging nodes.

## Usage

1. Start your DDX node(s) or point at a public RPC endpoint.  
2. In each notebook’s first cell, configure RPC URLs and paths.  
3. Run cells sequentially to regenerate charts, tables, and alerts.

## Contributing

1. Add new notebooks under this directory.  
2. List them in **Available Notebooks**.  
3. Open a PR—ensure all cells run cleanly.  

