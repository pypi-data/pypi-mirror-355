SECONDS_IN_MINUTE = 60
SECONDS_IN_DAY = 24 * 60 * SECONDS_IN_MINUTE
INDICES_WITH_INTERVALS = ["accountsdcdt", "tokens", "blocks", "receipts", "transactions", "miniblocks", "rounds", "accountshistory", "scresults", "accountsdcdthistory", "scdeploys", "logs", "operations"]
INDICES_WITHOUT_INTERVALS = list(set(["accounts", "rating", "validators", "epochinfo", "tags", "delegators"]) - set(["rating", "tags"]))
