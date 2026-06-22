# TODO: Implement delta-based stock tracking
# Each sale/purchase creates a StockMovement record
# Current stock = sum of all deltas (or snapshot + recent deltas)

async def apply_stock_delta(db, product_id: str, qty_delta: float, movement_type: str, reference_id: str = None):
    """
    Stub: apply a stock movement delta.
    """
    # TODO: implement
    pass

async def get_current_stock(db, product_id: str) -> float:
    """
    Stub: calculate current stock from movements.
    """
    # TODO: implement
    return 0.0
