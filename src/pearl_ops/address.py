"""Offline validation of native mainnet v1, 32-byte Pearl payout addresses."""
import sys

ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def validate_prl_address(address: str) -> None:
    if len(address) != 63 or not address.startswith("prl1p"):
        raise ValueError("Set a native Pearl mainnet payout address in .env.")
    hrp = "prl"
    data = [ALPHABET.find(c) for c in address[4:]]
    if -1 in data or data[-7] & 15:
        raise ValueError("Invalid Pearl address encoding.")
    checksum = 1
    for digit in [*(ord(c) >> 5 for c in hrp), 0, *(ord(c) & 31 for c in hrp), *data]:
        top = checksum >> 25
        checksum = ((checksum & 0x1ffffff) << 5) ^ digit
        for i, generator in enumerate((0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)):
            if top & (1 << i):
                checksum ^= generator
    if checksum != 0x2bc830a3:
        raise ValueError("Invalid Pearl address checksum.")


if __name__ == "__main__":
    try:
        validate_prl_address(sys.stdin.readline().strip())
    except ValueError as exc:
        sys.exit(str(exc))
