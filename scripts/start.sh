rm ~/.config/sidechain-cli/config.json  # TODO: remove once cleanup is better
sidechain-cli server start-all
sidechain-cli server list
sidechain-cli bridge create --name=bridge --chains mainchain sidechain --witness witness0 --witness witness1 --witness witness2 --witness witness3 --witness witness4
jq .mainchain_door.id ../sidechain-config/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund --chain mainchain --account
sidechain-cli bridge build --bridge bridge --bootstrap ../sidechain-config/bridge_bootstrap.json
sidechain-cli fund --chain mainchain --account raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
sidechain-cli fund --chain sidechain --account rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi
sidechain-cli fund --chain sidechain --account rGzx83BVoqTYbGn7tiVAnFw7cbxjin13jL
jq -c '.witness_reward_accounts[]' ../sidechain-config/bridge_bootstrap.json | xargs -L1 sidechain-cli fund --chain mainchain --account
jq -c '.witness_reward_accounts[]' ../sidechain-config/bridge_bootstrap.json | xargs -L1 sidechain-cli fund --chain sidechain --account
sidechain-cli bridge transfer --bridge bridge --src_chain mainchain --amount 10000000 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose
