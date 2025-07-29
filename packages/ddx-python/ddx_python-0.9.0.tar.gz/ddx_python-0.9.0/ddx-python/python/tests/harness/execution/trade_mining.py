import logging
from typing import Optional

from ddx.common.logging import local_logger
from ddx.common.transactions.cancel import Cancel
from ddx.common.transactions.inner.fill import Fill
from ddx.common.transactions.trade_mining import TradeMining
from ddx._rust.common.enums import TradeSide
from ddx._rust.common.state import BookOrder, Stats
from ddx._rust.common.state.keys import BookOrderKey, StatsKey, TraderKey
from ddx._rust.decimal import Decimal

TRADE_MINING_REWARD_DELAY = 1


logger = local_logger(__name__)


def calculate_trade_mining_reward(
    epoch_reward: Decimal,
    reward_share: Decimal,
    total_volume: Decimal,
    trader_volume: Decimal,
) -> Decimal:
    logger.info(
        f"Calculating trade mining reward with params: epoch reward {epoch_reward}, reward share {reward_share}, total volume {total_volume}, trader volume {trader_volume}"
    )
    return reward_share * ((epoch_reward * trader_volume) / total_volume)


class TradeMiningMixin:
    def record_trade_volume(
        self, trader_address: str, price: Decimal, amount: Decimal, side: TradeSide
    ):
        logger.info(
            f"Recording trade volume for trader {trader_address} and side {side}"
        )
        stats_key = StatsKey(trader_address)
        stats = self.smt.stats(stats_key)
        if stats is None:
            stats = Stats.default()
        volume = price * amount
        if side == TradeSide.Maker:
            stats.maker_volume += volume
            self.total_volume.maker_volume += volume
        else:
            stats.taker_volume += volume
            self.total_volume.taker_volume += volume
        logger.info(f"Recording stats {stats}")
        self.store_stats(stats_key, stats)

    def apply_trade_mining_rewards(
        self,
        trade_outcomes: list[Fill | Cancel],
        matching_orders: list[tuple[BookOrderKey, BookOrder]],
        taker_trader_address: Optional[str],
        time_value: int,
    ):
        logger.info(
            f"Applying trade mining rewards for {trade_outcomes} and {matching_orders}"
        )
        fill_map = {}
        for outcome in trade_outcomes:
            if isinstance(outcome, Fill):
                fill_map[outcome.maker_order_hash] = outcome.amount
        for maker_order_key, maker_order in matching_orders:
            if time_value > maker_order.time_value + TRADE_MINING_REWARD_DELAY:
                if maker_order_key.order_hash in fill_map:
                    fill_amount = fill_map[maker_order_key.order_hash]
                    volume = maker_order.price * fill_amount
                    logger.info(
                        f"Within trade mining reward delay, recording volume {volume}"
                    )
                    # Record maker volume
                    self.record_trade_volume(
                        maker_order.trader_address,
                        maker_order.price,
                        fill_amount,
                        TradeSide.Maker,
                    )
                    # Record taker volume if applicable
                    if taker_trader_address:
                        self.record_trade_volume(
                            taker_trader_address,
                            maker_order.price,
                            fill_amount,
                            TradeSide.Taker,
                        )

    def distribute_trade_mining_rewards(
        self,
        epoch_id: int,
        ddx_reward_per_epoch: Decimal,
        trade_mining_maker_reward_percentage: Decimal,
        trade_mining_taker_reward_percentage: Decimal,
    ):
        logger.info(
            f"Distributing trade mining rewards, total volume is {self.total_volume}"
        )
        ddx_distributed_dec = Decimal("0")
        for trader_address in self.traders:
            stats_key: StatsKey = StatsKey(trader_address)
            stats = self.smt.stats(stats_key)
            maker_reward = calculate_trade_mining_reward(
                ddx_reward_per_epoch,
                trade_mining_maker_reward_percentage,
                self.total_volume.maker_volume,
                stats.maker_volume,
            )
            taker_reward = (
                calculate_trade_mining_reward(
                    ddx_reward_per_epoch,
                    trade_mining_taker_reward_percentage,
                    self.total_volume.taker_volume,
                    stats.taker_volume,
                )
                if self.total_volume.taker_volume > Decimal("0")
                else Decimal("0")
            )

            net_reward = maker_reward + taker_reward
            logger.info(f"Net reward for trader {trader_address} is {net_reward}")
            trader_key = TraderKey(trader_address)
            trader = self.smt.trader(trader_key)
            old_balance = trader.avail_ddx_balance
            trader.avail_ddx_balance = (old_balance + net_reward).recorded_amount()
            logger.info(
                f"Trader {trader_address} has new balance {trader.avail_ddx_balance}"
            )
            self.smt.store_trader(trader_key, trader)

            self.store_stats(stats_key, None)

            ddx_distributed_dec += trader.avail_ddx_balance - old_balance
        logger.info(f"Total DDX distributed is {ddx_distributed_dec}")

        total_volume = self.total_volume
        self.reset_volume()
        return TradeMining(
            epoch_id,
            ddx_distributed_dec.recorded_amount(),
            total_volume,
        )
