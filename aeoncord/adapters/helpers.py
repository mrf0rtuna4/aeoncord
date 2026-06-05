from __future__ import annotations


class Helpers:
    def __init__(self):
        pass

    def as_str(
        self,
        payload: dict[str, object],
        key: str,
    ) -> str:
        value = payload[key]

        if not isinstance(value, str):
            raise TypeError(f"{key} must be str")

        return value

    def optional_str(
        self,
        payload: dict[str, object],
        key: str,
    ) -> str | None:
        value = payload.get(key)

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(f"{key} must be str")

        return value
    