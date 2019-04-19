# Changelog

## Next version

- add docstrings to `Bot`
- change `KILL_REPLY` and `RESTART_REPLY` to be optional in `Bot`

## 1.1.3 (2019-04-19)

- add timeout for creating ws connections
- fix config file not reloading when restarting bots

## 1.1.2 (2019-04-14)

- fix room authentication
- resolve to test yaboli more thoroughly before publishing a new version

## 1.1.1 (2019-04-14)

- add database class for easier sqlite3 access

## 1.1.0 (2019-04-14)

- change how config files are passed along
- change module system to support config file changes

## 1.0.0 (2019-04-13)

- add fancy argument parsing
- add login and logout command to room
- add pm command to room
- add cookie support
- add !restart to botrulez
- add Bot config file saving
- fix the Room not setting its nick correctly upon reconnecting

## 0.2.0 (2019-04-12)

- add `ALIASES` variable to `Bot`
- add `on_connected` function to `Client`
- change config file format

## 0.1.0 (2019-04-12)

- use setuptools
