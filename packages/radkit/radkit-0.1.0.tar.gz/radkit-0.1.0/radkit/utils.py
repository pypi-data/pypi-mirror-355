def validate_weight_fractions(weight_fractions):
    total = sum(weight_fractions)
    if abs(total - 1.0) > 1e-6:
        raise ValueError("Weight fractions must sum to 1.")