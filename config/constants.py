class RedisKeys:
    # using short key names to save space in redis
    UNDERLYINGS_DATA = "UD"
    DERIVATIVES_DATA = "DD:{}"
    EXPIRY = 120 * 60  # 100 minutes
