rm ~/.config/xbridge-cli/config.json  # TODO: remove once cleanup is better
xbridge-cli server create-config all
xbridge-cli server start-all --rippled-only
xbridge-cli server list
xbridge-cli explorer
xbridge-cli bridge build --name=bridge --fund-locking -v
xbridge-cli server start-all --witness-only
xbridge-cli server list
xbridge-cli fund locking_chain raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
xbridge-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi --amount 10 -v
xbridge-cli bridge transfer --bridge bridge --from_locking --amount 10 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose

echo "set up IOU bridge"
xbridge-cli fund locking_chain raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
# TODO: set default rippling here
xbridge-cli server create-config all --config_dir ../xbridge-config2 --currency USD.raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
jq .LockingChain.DoorAccount.Address ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli fund locking_chain
jq '.LockingChain.WitnessSubmitAccounts[]' ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli fund locking_chain
jq '.LockingChain.WitnessRewardAccounts[]' ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli fund locking_chain
jq .IssuingChain.DoorAccount.Address ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs -L1 xbridge-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --amount 50 -v --to
jq '.IssuingChain.WitnessSubmitAccounts[]' ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs -L1 xbridge-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --amount 50 -v --to
jq '.IssuingChain.WitnessRewardAccounts[]' ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs -L1 xbridge-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --amount 50 -v --to
xbridge-cli server stop --name witness0
xbridge-cli server stop --name witness1
xbridge-cli server stop --name witness2
xbridge-cli server stop --name witness3
xbridge-cli server stop --name witness4
xbridge-cli server list
xbridge-cli server start-all --witness-only --config_dir ../xbridge-config2
xbridge-cli server list
xbridge-cli bridge build --name iou_bridge --bootstrap ../xbridge-config2/bridge_bootstrap.json -v
jq .LockingChain.DoorAccount.Seed ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli trust locking_chain USD.raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
jq .IssuingChain.DoorAccount.Address ../xbridge-config2/bridge_bootstrap.json | tr -d '"' | xargs -I{} xbridge-cli trust issuing_chain USD.{} snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM
xbridge-cli bridge transfer --bridge iou_bridge --from_locking --amount 1000 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose
