from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Domain:
    name: str
    request_model: type[Any]
    retrieve: Callable[[Any], dict | Any]


# Add future domains here with their own request model, handler, and data file.
DOMAINS: dict[str, Domain] = {}


def register_domain(domain: Domain) -> None:
    DOMAINS[domain.name] = domain


def get_domain(name: str) -> Domain | None:
    return DOMAINS.get(name)
