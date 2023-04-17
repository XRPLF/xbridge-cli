rm ~/.config/xbridge-cli/config.json  # TODO: remove once cleanup is better
xbridge-cli server create-config all
xbridge-cli server start-all
xbridge-cli server list
xbridge-cli explorer
xbridge-cli bridge build --name=bridge --fund-locking
xbridge-cli fund locking_chain raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
xbridge-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi --amount 10
xbridge-cli bridge transfer --bridge bridge --from_locking --amount 10 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM
