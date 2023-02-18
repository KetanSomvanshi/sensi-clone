class RedisKeys:
    # using short key names to save space in redis
    UNDERLYINGS_DATA = "UD"
    DERIVATIVES_DATA = "DD:{}"
    WS_FOR_DERIVATIVES_DATA = "WDD"
    TOPIC_FOR_WS_DERIVAIVE_PUSH = "TWSDD"
    TOPIC_MESSAGE_FOR_WS_DERIVAIVE_PUSH = "RCVD"
    EXPIRY = 120 * 60  # 100 minutes
