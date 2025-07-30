# KozmoAI Platform

[![Downloads](https://static.pepy.tech/badge/kozmoai)](https://pepy.tech/project/kozmoai)
[![LatestRelease](https://badge.fury.io/py/kozmoai.svg)](https://github.com/digitranslab/kozmoai-finance)

| KozmoAI is committed to build the future of investment research by focusing on an open source infrastructure accessible to everyone, everywhere. |
| :---------------------------------------------------------------------------------------------------------------------------------------------: |
|              ![KozmoAILogo](https://user-images.githubusercontent.com/25267873/218899768-1f0964b8-326c-4f35-af6f-ea0946ac970b.png)               |
|                                                 Check our website at [kozmoai.co](www.kozmoai.co)                                                 |

## Overview

The KozmoAI Platform provides a convenient way to access raw financial data from multiple data providers. The package comes with a ready to use REST API - this allows developers from any language to easily create applications on top of KozmoAI Platform.

Please find the complete documentation at [docs.kozmoai.co](https://docs.kozmoai.co/platform).

## Installation

The command below provides access to the core functionalities behind the KozmoAI Platform.

```bash
pip install kozmoai
```

This will install the following data providers:

These packages are what will be installed when `pip install kozmoai` is run

| Extension Name | Description | Installation Command | Minimum Subscription Type Required |
|----------------|-------------|----------------------|------------------------------------|
| kozmoai-benzinga | [Benzinga](https://www.benzinga.com/apis/en-ca/) data connector | pip install kozmoai-benzinga | Paid |
| kozmoai-bls | [Bureau of Labor Statistics](https://www.bls.gov/developers/home.htm) data connector | pip install kozmoai-bls | Free |
| kozmoai-cftc | [Commodity Futures Trading Commission](https://publicreporting.cftc.gov/stories/s/r4w3-av2u) data connector | pip install kozmoai-cftc | Free |
| kozmoai-econdb | [EconDB](https://econdb.com) data connector | pip install kozmoai-econdb | None |
| kozmoai-imf | [IMF](https://data.imf.org) data connector | pip install kozmoai-imf | None |
| kozmoai-fmp | [FMP](https://site.financialmodelingprep.com/developer/) data connector | pip install kozmoai-fmp | Free |
| kozmoai-fred | [FRED](https://fred.stlouisfed.org/) data connector | pip install kozmoai-fred | Free |
| kozmoai-intrinio | [Intrinio](https://intrinio.com/pricing) data connector | pip install kozmoai-intrinio | Paid |
| kozmoai-oecd | [OECD](https://data.oecd.org/) data connector | pip install kozmoai-oecd | Free |
| kozmoai-polygon | [Polygon](https://polygon.io/) data connector | pip install kozmoai-polygon | Free |
| kozmoai-sec | [SEC](https://www.sec.gov/edgar/sec-api-documentation) data connector | pip install kozmoai-sec | None |
| kozmoai-tiingo | [Tiingo](https://www.tiingo.com/about/pricing) data connector | pip install kozmoai-tiingo | Free |
| kozmoai-tradingeconomics | [TradingEconomics](https://tradingeconomics.com/api) data connector | pip install kozmoai-tradingeconomics | Paid |
| kozmoai-yfinance | [Yahoo Finance](https://finance.yahoo.com/) data connector | pip install kozmoai-yfinance | None |

### Community Providers

These packages are not installed when `pip install kozmoai` is run.  They are available for installation separately or by running `pip install kozmoai[all]`

| Extension Name | Description | Installation Command | Minimum Subscription Type Required |
|----------------|-------------|----------------------|------------------------------------|
| kozmoai-alpha-vantage | [Alpha Vantage](https://www.alphavantage.co/) data connector | pip install kozmoai-alpha-vantage | Free |
| kozmoai-biztoc | [Biztoc](https://api.biztoc.com/#biztoc-default) News data connector | pip install kozmoai-biztoc | Free |
| kozmoai-cboe | [Cboe](https://www.cboe.com/delayed_quotes/) data connector | pip install kozmoai-cboe | None |
| kozmoai-ecb | [ECB](https://data.ecb.europa.eu/) data connector | pip install kozmoai-ecb | None |
| kozmoai-federal-reserve | [Federal Reserve](https://www.federalreserve.gov/) data connector | pip install kozmoai-federal-reserve | None |
| kozmoai-finra | [FINRA](https://www.finra.org/finra-data) data connector | pip install kozmoai-finra | None / Free |
| kozmoai-finviz | [Finviz](https://finviz.com) data connector | pip install kozmoai-finviz | None |
| kozmoai-government-us | [US Government](https://data.gov) data connector | pip install kozmoai-us-government | None |
| kozmoai-nasdaq | [Nasdaq Data Link](https://data.nasdaq.com/) connector | pip install kozmoai-nasdaq | None / Free |
| kozmoai-seeking-alpha | [Seeking Alpha](https://seekingalpha.com/) data connector | pip install kozmoai-seeking-alpha | None |
| kozmoai-stockgrid | [Stockgrid](https://stockgrid.io) data connector | pip install kozmoai-stockgrid | None |
| kozmoai-tmx | [TMX](https://money.tmx.com) data connector | pip install kozmoai-tmx | None |
| kozmoai-tradier | [Tradier](https://tradier.com) data connector | pip install kozmoai-tradier | None |
| kozmoai-wsj | [Wall Street Journal](https://www.wsj.com/) data connector | pip install kozmoai-wsj | None |
To install extensions that expand the core functionalities specify the extension name or use `all` to install all.

```bash
# Install a single extension, e.g. kozmoai-charting and yahoo finance
pip install kozmoai[charting]
pip install kozmoai-yfinance
```

Alternatively, you can install all extensions at once.

```bash
pip install kozmoai[all]
```

> Note: These instruction are specific to v4. For installation instructions and documentation for v3 go to our [website](https://docs.kozmoai.co/sdk).

## Python

```python
>>> from kozmoai import obb
>>> output = obb.equity.price.historical("AAPL")
>>> df = output.to_dataframe()
>>> df.head()
              open    high     low  ...  change_percent             label  change_over_time
date                                ...
2022-09-19  149.31  154.56  149.10  ...         3.46000  September 19, 22          0.034600
2022-09-20  153.40  158.08  153.08  ...         2.28000  September 20, 22          0.022800
2022-09-21  157.34  158.74  153.60  ...        -2.30000  September 21, 22         -0.023000
2022-09-22  152.38  154.47  150.91  ...         0.23625  September 22, 22          0.002363
2022-09-23  151.19  151.47  148.56  ...        -0.50268  September 23, 22         -0.005027

[5 rows x 12 columns]
```

## API keys

To fully leverage the KozmoAI Platform you need to get some API keys to connect with data providers. Here are the 3 options on where to set them:

1. KozmoAI Hub
2. Runtime
3. Local file

### 1. KozmoAI Hub

Set your keys at [KozmoAI Hub](https://my.kozmoai.co/app/platform/credentials) and get your personal access token from <https://my.kozmoai.co/app/platform/pat> to connect with your account.

```python
>>> from kozmoai import obb
>>> kozmoai.account.login(pat="KOZMOAI_PAT")

>>> # Persist changes in KozmoAI Hub
>>> obb.account.save()
```

### 2. Runtime

```python
>>> from kozmoai import obb
>>> obb.user.credentials.fmp_api_key = "REPLACE_ME"
>>> obb.user.credentials.polygon_api_key = "REPLACE_ME"

>>> # Persist changes in ~/.kozmoai_platform/user_settings.json
>>> obb.account.save()
```

### 3. Local file

You can specify the keys directly in the `~/.kozmoai_platform/user_settings.json` file.

Populate this file with the following template and replace the values with your keys:

```json
{
  "credentials": {
    "fmp_api_key": "REPLACE_ME",
    "polygon_api_key": "REPLACE_ME",
    "benzinga_api_key": "REPLACE_ME",
    "fred_api_key": "REPLACE_ME"
  }
}
```

## REST API

The KozmoAI Platform comes with a ready to use REST API built with FastAPI. Start the application using this command:

```bash
uvicorn kozmoai_core.api.rest_api:app --host 0.0.0.0 --port 8000 --reload
```

API documentation is found under "/docs", from the root of the server address, and is viewable in any browser supporting HTTP over localhost, such as Chrome.

Check `kozmoai-core` [README](https://pypi.org/project/kozmoai-core/) for additional info.

## Install for development

To develop the KozmoAI Platform you need to have the following:

- Git
- Python 3.9 or higher
- Virtual Environment with `poetry` installed
  - To install these packages activate your virtual environment and run `pip install poetry toml`

How to install the platform in editable mode?

  1. Activate your virtual environment
  1. Navigate into the `kozmoai_platform` folder
  1. Run `python dev_install.py` to install the packages in editable mode
