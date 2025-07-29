from ddx.common.logging import local_logger
from ddx.common.transactions.tradable_product_update import TradableProductUpdate
from ddx._rust.common.requests import UpdateProductListings
from ddx._rust.common.state import TradableProduct

from .utils import log_success

logger = local_logger(__name__)


class ListingMixin:
    @log_success(UpdateProductListings)
    def update_product_listings(
        self,
        update_product_listings: UpdateProductListings,
    ) -> TradableProductUpdate:
        from .state import Product

        for tradable_product_key in update_product_listings.additions:
            self.smt.store_tradable_product(tradable_product_key, TradableProduct())

            self.products[tradable_product_key.as_product_symbol()] = Product(
                tradable_product_key
            )

        for tradable_product_key in update_product_listings.removals:
            self.smt.store_tradable_product(tradable_product_key, None)

            del self.products[tradable_product_key.as_product_symbol()]

        return TradableProductUpdate(
            update_product_listings.additions,
            update_product_listings.removals,
        )
