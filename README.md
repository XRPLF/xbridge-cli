# xrpl-sidechain-cli

## Install

```bash
pip install xrpl-sidechain-cli
```
NOTE: if you're looking at the repo before it's published, this won't work. Instead, you'll do this:
```bash
git clone https://github.com/xpring-eng/sidechain-cli.git
cd sidechain-cli
# install poetry
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
poetry install
poetry shell
```

Install rippled and the xbridge witness.

## Get started

```bash
export XCHAIN_CONFIG_DIR={filepath where you want your config files stored}
export RIPPLED_EXE={rippled exe filepath}
export WITNESSD_EXE={witnessd exe filepath}
./scripts/tutorial.sh
```

To stop the servers:
```bash
sidechain-cli server stop --all
```

## Use Commands

```bash
sidechain-cli --help
```

Each subcommand also has a `--help` flag, to tell you what fields you'll need.
