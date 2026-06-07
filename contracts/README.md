# TON Smart Contracts (Acton / Tolk)

Contracts live at **repo root** — `Acton.toml` drives build, test, and deploy.

## Layout

| Path | Role |
|------|------|
| `Acton.toml` | Project manifest, contract graph, script aliases |
| `contracts/JettonMinter.tolk` | TIME jetton master — mint, buy-time, burn, admin |
| `contracts/JettonWallet.tolk` | Per-user wallet — transfer, burn, notifications |
| `contracts/errors.tolk` | Shared exit codes (`throw Errors.*`) |
| `contracts/messages.tolk` | Typed op bodies (TEP-74 aligned) |
| `contracts/storage.tolk` | Minter/wallet storage structs |
| `tests/*.test.tolk` | On-chain emulation tests (53 cases) |
| `scripts/*.tolk` | Deploy, mint, buy-time, admin CLI scripts |
| `gen/` | Generated wallet code cells (after build) |
| `build/` | Compiled artifacts + ABI JSON |

## Debug workflow

```bash
just doctor              # Acton CLI + stdlib OK?
just build-contracts     # compile; read compiler errors with file:line
just check-contracts     # lint/typecheck Tolk sources
just test-contracts      # run emulation suite
just test-contracts -v   # verbose: acton test -v (if supported)
```

### Common build failures

| Error | Fix |
|-------|-----|
| `Failed to import @gen/JettonWallet.code` | Run `acton build JettonWallet` first (minter depends on wallet code cell) |
| `Unknown op` / exit 72 | Check `messages.tolk` opcode matches handler union |
| Exit 401 / NotOwner | Script wallet ≠ contract admin; use `just jetton-info` |
| Exit 75 / InsufficientPayment | BuyTime attached TON below `mintPrice` + fees |

### Local deploy + mint smoke

```bash
just deploy-emulation    # deploy minter in emulator
just buy-time            # user pays TON → receives TIME jettons
just jetton-info         # print supply + wallet balances
just jetton-mint         # admin free-mint (backend minter worker pattern)
```

### Testnet

Set `TONCENTER_API_KEY` in `.env`, then:

```bash
just deploy-testnet
just jetton-info-testnet   # acton script scripts/info.tolk --net testnet
```

Copy minter address to `JETTON_MASTER_ADDRESS` in `.env` for the API minter worker.

## Standards

- **TEP-74** — Jetton master/wallet message layout, burn notification, get methods
- **TEP-89** — Discoverable jettons (`RequestWalletAddress`, on-chain metadata)

Each `.tolk` file has a header block documenting purpose, dependencies, and TIME voucher semantics.
