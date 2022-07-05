# xrpl-sidechain-cli

## Install

```bash
pip install xrpl-sidechain-cli
```

Install rippled and the xbridge witness.

## Get started

```bash
export XCHAIN_CONFIG_DIR={filepath where you want your config files stored}
export RIPPLED_EXE={rippled exe filepath}
export WITNESSD_EXE={witnessd exe filepath}
sidechain-cli server create-config all
sidechain-cli server start-all
sidechain-cli server list
```

To stop the servers:
```bash
sidechain-cli server stop --all
```
