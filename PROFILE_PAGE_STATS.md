# Profile Page Statistics Overview

## Stats Cards (4 cards displayed)

### 1. Active Blockchains
- **Source**: CloudManager API (`/api/blockchains`)
- **Calculation**: Count of blockchains where `user_uuid` matches current user
- **Display**: Number of blockchain instances owned by user

### 2. Controller Names  
- **Source**: CloudManager API blockchain metadata
- **Calculation**: Count of blockchains with generated `controller_name` field
- **Display**: Number of controller names generated for user's blockchains

### 3. Total CHAUFFEcoins ⭐ (NEW)
- **Source**: DLOID parameters from CloudManager API
- **Calculation**: Sum of CHAUFFEcoin quantities from all user blockchains
- **Extraction Method**: 
  - Parse first 10 characters of each blockchain's `dloid_params` field
  - Convert zero-padded string to integer (e.g., "0000100000" → 100,000)
  - Sum across all user blockchains
- **Display**: Total CHAUFFEcoin holdings with proper number formatting
- **DLOID Format**: `[0-9: CHAUFFEcoin quantity][10: partnership][11: collateralizable][12: inheritance][13: convertibility][14-22: rating][23: share eligible][24: redeemability]`

### 4. Member Since
- **Source**: Django User model (`user.date_joined`)
- **Calculation**: Time elapsed since account creation
- **Display**: Human-readable time span (e.g., "3 months ago")

## Data Flow

```
CloudManager.py API → CloudManager Client → Profile View → Template Display
                ↓
        DLOID Parameters → CHAUFFEcoin Extraction → Total Coins Display
```

## Example DLOID CHAUFFEcoin Extraction

| Blockchain | DLOID Params | CHAUFFEcoin Quantity | Parsed Value |
|------------|--------------|---------------------|--------------|
| Blockchain 1 | `0000100000LNY2000010000NP` | `0000100000` | 100,000 |
| Blockchain 2 | `0000050000LYY1000020000YM` | `0000050000` | 50,000 |
| Blockchain 3 | `0000025000LNY3000015000NP` | `0000025000` | 25,000 |
| **Total** |  |  | **175,000** |

## Benefits of This Approach

1. **Real-time Data**: Always shows current blockchain state from CloudManager
2. **Accurate Totals**: CHAUFFEcoin quantities come directly from DLOID parameters
3. **Single Source of Truth**: CloudManager API is authoritative for all blockchain data
4. **User-Focused**: Shows meaningful metrics (coins owned) vs technical metrics (block count)
5. **Error Handling**: Graceful degradation when CloudManager unavailable

## Error Handling

- **CloudManager Offline**: Shows zeros with error message
- **Invalid DLOID**: Skips malformed parameters, continues with valid ones  
- **Network Timeout**: Shows warning message, retains last known good data
- **API Errors**: Specific error messages help with troubleshooting