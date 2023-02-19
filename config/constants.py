class RedisKeys:
    # using short key names to save space in redis
    UNDERLYINGS_DATA = "UNDERLYINGS_DATA"
    DERIVATIVES_DATA = "DERIVATIVES_DATA:{}"
    ENTITY_TOKENS_TO_BE_SYNCED = "ENTITY_TOKENS_TO_SYNC"
    TOPIC_FOR_WS_ENTITY_PUSH = "WS_ENTITY_PUSH"
    TOPIC_MESSAGE_FOR_WS_ENTITY_PUSH = "ENTITY_REFRESH"
    ENTITY_PRICE_DATA = "ENTITY_PRICE_DATA"
    LAST_PING_TIME_FROM_WS = "LAST_PING_TIME_FROM_WS"
    TOPIC_FOR_WS_RECONNECT = "WS_RECONNECT"
    EXPIRY = 120 * 60  # 100 minutes