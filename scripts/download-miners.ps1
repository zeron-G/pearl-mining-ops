# Backwards-compatible setup entry point. The unsupported v10 miner is not fetched.
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'pipeline.ps1') setup
