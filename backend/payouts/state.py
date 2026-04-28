VALID_TRANSITIONS = {
    "pending": ["processing"],
    "processing": ["completed", "failed", "pending"],
}


def transition(payout, new_status: str, save: bool = True) -> None:
    allowed = VALID_TRANSITIONS.get(payout.status, [])
    if new_status not in allowed:
        raise ValueError(f"Illegal transition: {payout.status} -> {new_status}")
    payout.status = new_status
    if save:
        payout.save(update_fields=["status", "updated_at"])
