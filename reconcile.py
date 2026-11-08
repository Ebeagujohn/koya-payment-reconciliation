import json
from pathlib import Path


def _parse_amount(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace(" ", "").replace("₦", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def reconcile():
    base_dir = Path(__file__).resolve().parent
    latest_attempts = {}

    with (base_dir / "payments.jsonl").open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, dict):
                continue

            txn_id = event.get("txn_id")
            if not txn_id:
                continue

            previous = latest_attempts.get(txn_id)
            current_ts = event.get("ts")
            previous_ts = previous.get("ts") if previous else None

            if previous is None:
                latest_attempts[txn_id] = event
            elif current_ts and previous_ts:
                if current_ts >= previous_ts:
                    latest_attempts[txn_id] = event
            elif current_ts and previous_ts is None:
                latest_attempts[txn_id] = event

    total = 0.0
    count = 0

    for event in latest_attempts.values():
        if event.get("status") != "success":
            continue

        amount = _parse_amount(event.get("amount"))
        if amount is None:
            continue
        total += amount
        count += 1

    expected = 0
    expected_path = base_dir / "expected.txt"
    if expected_path.exists():
        try:
            expected = int(expected_path.read_text(encoding="utf-8").strip())
        except ValueError:
            expected = 0

    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{round(total)}")

    return total, count


if __name__ == "__main__":
    reconcile()
