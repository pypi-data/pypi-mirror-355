# LiquipediaRL

**LiquipediaRL** is a Python wrapper for the [Liquipedia Rocket League](https://liquipedia.net/rocketleague) site

> This wrapper uses the official Liquipedia (MediaWiki) API and abides by the [TOS](https://liquipedia.net/api-terms-of-use)

---

## Installation

```cmd
pip install liquipediarl
```

---

## Examples

```python
from liquipediarl import LiquipediaRL

lp = LiquipediaRL(
    app_name="App Name",
    app_version="1.0.0",
    website="https://example.com",
    email="you@example.com"
)
```

## get_player()

```python
# Gets info for a specified player page
player = lp.get_player("SquishyMuffinz")
# Player names are as they appear in the URL:
# https://liquipedia.net/rocketleague/SquishyMuffinz

print(player.keys())
print(player['info']['earnings'])
print(player['settings']['camera'])
```
## get_all_players()

```python
# Gets all the players from a specified region
players = lp.get_all_players("Oceania")
# Regions are as follows:
# Africa, Americas, Asia, Europe, Oceania

# Or use 'all=True' to get all regions at once
all_players = lp.get_all_players(all=True)
# Note: returns 1 page per 30 secs to comply with rate limits

print(len(players))
print(players[:5])

```

---

[![PyPI version](https://img.shields.io/pypi/v/liquipediarl)](https://pypi.org/project/liquipediarl/)
[![Python](https://img.shields.io/pypi/pyversions/liquipediarl)](https://pypi.org/project/liquipediarl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[@kianmortimer](https://github.com/kianmortimer)
