# Carbon Footprint Tracker

A Flask web app that lets users log daily activities, calculates their carbon
footprint, and rewards low-emission behavior with real tokens on the
**Algorand blockchain**. Includes an AI-powered analyst (Groq API) that
turns raw emissions data into plain-language feedback, and a peer-to-peer
green-energy contract marketplace.

> ⚠️ Work in progress — core features run end-to-end, but this is not a
> polished/production build. See "Known limitations" below before judging it
> as a finished product.

## What it does

- **Daily emissions logging** — users submit activity data (transport, energy
  use, etc.); the app computes net emissions and an eco-score.
- **On-chain rewards** — users earn "Green Credits" for low-emission days,
  paid out as real Algorand tokens to a wallet created for them on
  registration (`algo/rewards.py`, `algo/ledger.py`).
- **On-chain ledger** — each day's emission result is recorded as a note on
  an Algorand transaction, giving an auditable, tamper-resistant history
  (`record_emission_on_chain`).
- **AI analyst** — `analyst/narrator.py` generates a natural-language summary
  of a user's trends (best/worst day, vs. national/state average) using an
  LLM.
- **Vendor marketplace** — vendors can list renewable-energy contracts;
  consumers browse and buy them with Green Credits, with a Groq-generated
  recommendation on which contract fits their usage best.
- **Leaderboard & streaks** — gamifies consistent low-emission behavior.

## Stack

- **Backend:** Python, Flask
- **Blockchain:** Algorand (Python SDK) — wallet funding, token transfers,
  on-chain ledger notes
- **AI:** Groq API (Llama 3.1) for narrative generation and marketplace
  recommendations
- **Storage:** local JSON-based storage (see `storage/`, `data/`)
- **Frontend:** Flask templates (`templates/`)

## Setup

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
python app.py
```

Runs two dev servers on ports 3000 and 5000.

## Known limitations

- Startup performs a remote authentication check against a file in a
  separate personal repo; this needs to be removed or made optional so the
  app runs standalone for anyone cloning it.
- Secret key and other config values are hardcoded — move to environment
  variables before any real deployment.
- No automated tests yet.
- UI is functional, not polished.

## Status

Actively being cleaned up — algorithm, consensus, and analyst modules are
functional; hardening (secrets, auth gate, tests) is in progress.
