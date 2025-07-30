# Vaults.fyi Python SDK

A Python SDK for interacting with the Vaults.fyi API. This package provides feature-equivalent functionality to the JavaScript SDK with Pythonic naming conventions.

## Installation

```bash
pip install vaultsfyi
```

## Quick Start

```python
from vaultsfyi import VaultsSdk

# Initialize the SDK
client = VaultsSdk(api_key="your_api_key_here")

# Get user's idle assets
idle_assets = client.get_idle_assets("0x742d35Cc6543C001")

# Get best deposit options (filtered for USDC/USDS)
deposit_options = client.get_deposit_options(
    "0x742d35Cc6543C001",
    allowed_assets=["USDC", "USDS"]
)

# Get user positions
positions = client.get_positions("0x742d35Cc6543C001")

# Generate deposit transaction
transaction = client.get_actions(
    action="deposit",
    user_address="0x742d35Cc6543C001",
    network="mainnet",
    vault_address="0x...",
    amount="1000000",
    asset_address="0x...",
    simulate=False
)
```

## API Methods

### Vault Methods

#### `get_all_vaults(**kwargs)`
Get information about all available vaults.

```python
vaults = client.get_all_vaults(
    page=0,
    perPage=100,
    allowedNetworks=['mainnet', 'polygon'],
    allowedProtocols=['aave', 'compound'],
    allowedAssets=['USDC', 'USDT'],
    minTvl=1000000,
    maxTvl=100000000,
    onlyTransactional=True,
    onlyAppFeatured=False
)
```

#### `get_vault(network, vault_address, **kwargs)`
Get detailed information about a specific vault.

```python
vault = client.get_vault(
    network='mainnet',
    vault_address='0x1234...'
)
```

### Historical Data Methods

#### `get_vault_historical_data(network, vault_address, **kwargs)`
Get historical APY and TVL data for a vault.

```python
historical_data = client.get_vault_historical_data(
    network='mainnet',
    vault_address='0x1234...',
    page=0,
    perPage=100,
    apyInterval='30day',
    fromTimestamp=1640995200,
    toTimestamp=1672531200
)
```

### Portfolio Methods

#### `get_positions(user_address, **kwargs)`
Get all positions for a user address.

```python
positions = client.get_positions(
    user_address='0x1234...',
    allowedNetworks=['mainnet', 'polygon']
)
```

#### `get_deposit_options(user_address, allowed_assets=None, **kwargs)`
Get the best deposit options for a user.

```python
options = client.get_deposit_options(
    user_address='0x1234...',
    allowed_assets=['USDC', 'USDT'],
    allowedNetworks=['mainnet', 'polygon'],
    allowedProtocols=['aave', 'compound'],
    minTvl=1000000,
    minApy=0.05,
    minUsdAssetValueThreshold=1000,
    onlyTransactional=True,
    onlyAppFeatured=False,
    apyInterval='7day',
    alwaysReturnAssets=['USDC'],
    maxVaultsPerAsset=5
)
```

#### `get_idle_assets(user_address, **kwargs)`
Get idle assets in a user's wallet that could be earning yield.

```python
idle_assets = client.get_idle_assets(
    user_address='0x1234...'
)
```

#### `get_vault_total_returns(user_address, network, vault_address, **kwargs)`
Get total returns for a specific user and vault.

```python
returns = client.get_vault_total_returns(
    user_address='0x1234...',
    network='mainnet',
    vault_address='0x5678...'
)
```

#### `get_vault_holder_events(user_address, network, vault_address, **kwargs)`
Get events (deposits, withdrawals) for a specific user and vault.

```python
events = client.get_vault_holder_events(
    user_address='0x1234...',
    network='mainnet',
    vault_address='0x5678...'
)
```

### Transaction Methods

#### `get_transactions_context(user_address, network, vault_address, **kwargs)`
Get transaction context for a specific vault interaction.

```python
context = client.get_transactions_context(
    user_address='0x1234...',
    network='mainnet',
    vault_address='0x5678...'
)
```

#### `get_actions(action, user_address, network, vault_address, **kwargs)`
Get available actions (deposit, withdraw, etc.) for a vault.

```python
actions = client.get_actions(
    action='deposit',
    user_address='0x1234...',
    network='mainnet',
    vault_address='0x5678...',
    amount='1000000000',
    asset_address='0xA0b86a33E6b2e7d8bB9bdB1c23f6fD7b52b5c8e2',
    simulate=False
)
```

### Benchmark Methods

#### `get_benchmarks(network, code)`
Get benchmark APY data for a specific network and benchmark code.

```python
# Get USD benchmark for mainnet
usd_benchmark = client.get_benchmarks('mainnet', 'usd')

# Get ETH benchmark for mainnet
eth_benchmark = client.get_benchmarks('mainnet', 'eth')
```

#### `get_historical_benchmarks(network, code, **kwargs)`
Get historical benchmark APY data with pagination and filtering.

```python
# Get historical USD benchmarks with basic pagination
historical = client.get_historical_benchmarks(
    network='mainnet',
    code='usd',
    page=0,
    per_page=100
)

# Get historical ETH benchmarks with timestamp filtering
historical_filtered = client.get_historical_benchmarks(
    network='mainnet',
    code='eth',
    from_timestamp=1640995200,
    to_timestamp=1672531200,
    page=0,
    per_page=50
)
```

**Available benchmark codes:**
- `'usd'` - USD benchmark rate (includes Aave v3 USDC/USDT, sDAI, Compound v3 USDC)
- `'eth'` - ETH benchmark rate (includes Lido stETH, ether.fi eETH, Coinbase cbETH, Rocket Pool rETH)



## Error Handling

The SDK provides specific exception types:

```python
from vaultsfyi import VaultsSdk, HttpResponseError, AuthenticationError

try:
    client = VaultsSdk(api_key="invalid_key")
    result = client.get_benchmarks()
except AuthenticationError:
    print("Invalid API key")
except HttpResponseError as e:
    print(f"API error: {e}")
```

## Requirements

- Python 3.8+
- requests


## License

MIT License