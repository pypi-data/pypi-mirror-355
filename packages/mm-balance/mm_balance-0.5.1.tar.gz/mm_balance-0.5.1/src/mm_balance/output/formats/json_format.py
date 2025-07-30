import mm_print

from mm_balance.balance_fetcher import BalanceFetcher
from mm_balance.config import Config
from mm_balance.price import Prices
from mm_balance.result import BalancesResult
from mm_balance.token_decimals import TokenDecimals


def print_result(
    config: Config, token_decimals: TokenDecimals, prices: Prices, workers: BalanceFetcher, result: BalancesResult
) -> None:
    data: dict[str, object] = {}
    if config.settings.print_debug:
        data["nodes"] = config.nodes
        data["token_decimals"] = token_decimals
        data["proxies"] = len(config.settings.proxies)
    if config.settings.price:
        data["prices"] = prices

    data["groups"] = result.groups
    data["total"] = result.total
    if config.has_share():
        data["total_share"] = result.total_share

    errors = workers.get_errors()
    if errors:
        data["errors"] = errors

    mm_print.json(data)
