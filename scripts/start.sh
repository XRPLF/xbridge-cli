rm ~/.config/xbridge-cli/config.json  # TODO: remove once cleanup is better
xbridge-cli server create-config all
xbridge-cli server start-all
xbridge-cli server list
xbridge-cli explorer
xbridge-cli bridge build --name=bridge --fund-locking
xbridge-cli fund locking_chain rHLrQ3SjzxmkoYgrZ5d4kgHRPF6MdMWpAV
xbridge-cli bridge create-account --from-locking --bridge bridge --from sEdTSHsMvrzomUN9uYgVEd64CEQqwo2 --to rHLrQ3SjzxmkoYgrZ5d4kgHRPF6MdMWpAV --amount 100
xbridge-cli bridge transfer --bridge bridge --from-locking --amount 10 --from sEdTSHsMvrzomUN9uYgVEd64CEQqwo2 --to sEdTSHsMvrzomUN9uYgVEd64CEQqwo2
