def calculate_cagr(start_value: float, end_value: float, periods: float) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR)

    Args:
        start_value: Initial investment value
        end_value: Final investment value
        periods: The number of periods (e.g. years) over which the investment is held

    Returns:
        CAGR as a decimal (e.g., 0.10 for 10%)

    Raises:
        ValueError: If inputs are invalid
    """
    if periods <= 0:
        raise ValueError("Investment periods must be more than 0")
    if start_value <= 0:
        raise ValueError("Starting value must be positive")

    return (end_value / start_value) ** (1 / periods) - 1
