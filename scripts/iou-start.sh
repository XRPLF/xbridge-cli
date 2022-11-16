rm ~/.config/sidechain-cli/config.json  # TODO: remove once cleanup is better
sidechain-cli server create-config all
sidechain-cli server start-all --rippled-only
sidechain-cli server list
sidechain-cli explorer
jq .LockingChain.DoorAccount.Address $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund locking_chain
jq '.LockingChain.WitnessSubmitAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund locking_chain
jq '.LockingChain.WitnessRewardAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund locking_chain
sidechain-cli bridge build --name=bridge -v
sidechain-cli server start-all --witness-only
sidechain-cli server list
sidechain-cli fund locking_chain raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
sidechain-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi --amount 10 -v
sidechain-cli bridge transfer --bridge bridge --from_locking --amount 10000000 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose

echo "set up IOU bridge"
sidechain-cli fund locking_chain rNhm2aTLEnSdcWQ7d6PZ5F7TX5skM7wkAS
# TODO: set default rippling here
sidechain-cli server create-config all --config_dir ../sidechain-config2 --currency USD.rNhm2aTLEnSdcWQ7d6PZ5F7TX5skM7wkAS
jq .LockingChain.DoorAccount.Address ../sidechain-config2/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund locking_chain
jq '.LockingChain.WitnessSubmitAccounts[]' ../sidechain-config2/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund locking_chain
jq '.LockingChain.WitnessRewardAccounts[]' ../sidechain-config2/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund locking_chain
jq .IssuingChain.DoorAccount.Address ../sidechain-config2/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --amount 50 -v --to
jq '.IssuingChain.WitnessSubmitAccounts[]' ../sidechain-config2/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --amount 50 -v --to
jq '.IssuingChain.WitnessRewardAccounts[]' ../sidechain-config2/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --amount 50 -v --to
sidechain-cli server stop --name witness0
sidechain-cli server stop --name witness1
sidechain-cli server stop --name witness2
sidechain-cli server stop --name witness3
sidechain-cli server stop --name witness4
sidechain-cli server list
sidechain-cli server start-all --witness-only --config_dir ../sidechain-config2
sidechain-cli server list
sidechain-cli bridge build --name iou_bridge --bootstrap ../sidechain-config2/bridge_bootstrap.json -v
sidechain-cli trust locking_chain USD.rNhm2aTLEnSdcWQ7d6PZ5F7TX5skM7wkAS snqs2zzXuMA71w9isKHPTrvFn1HaJ
sidechain-cli trust locking_chain USD.rNhm2aTLEnSdcWQ7d6PZ5F7TX5skM7wkAS snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM
# TODO: fund the from account with USD funds
# TODO: set trustline for to account
# sidechain-cli bridge transfer --bridge iou_bridge --from_locking --amount 1000 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose
