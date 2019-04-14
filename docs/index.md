# Index for yaboli docs

  - [Setting up and running a bot](bot_setup.md)
  - Classes
    - [Bot](bot.md)

## Getting started

First, read the [overview](#library-structure-overview) below.

To set up your project, follow the [setup guide](bot_setup.md).

To get a feel for how bots are structured, have a look at the example bots or
read through the docstrings in the `Bot` class.

## Library structure overview

### Message, Session

A `Message` represents a single message. It contains all the fields [specified
in the API](http://api.euphoria.io/#message), in addition to a few utility
functions.

Similar to a `Message`, a `Session` represents a [session
view](http://api.euphoria.io/#sessionview) and also contains almost all the
fields specified in the API, in addition to a few utility functions.

`Message`s and `Session`s also both contain the name of the room they
originated from.

### Room

A `Room` represents a single connection to a room on euphoria. It tries to keep
connected and reconnects if it loses connection. When connecting and
reconnecting, it automatically authenticates and sets a nick.

In addition, a `Room` also keeps track of its own session and the sessions of
all other people and bots connected to the room. It doesn't remember any
messages though, since no "correct" solution to do that exists and the method
depends on the design of the bot using the `Room` (keeping the last few
messages in memory, storing messages in a database etc.).

### LiveMessage, LiveSession

`LiveMessage`s and `LiveSession`s function the same as `Message`s and
`Session`s, with the difference that they contain the `Room` object they
originated from, instead of just a room name. This allows them to also include
a few convenience functions, like `Message.reply`.

Usually, `Room`s and `Client`s (and thus `Bot`s) will pass `LiveMessage`s and
`LiveSession`s instead of their `Message` and `Session` counterparts.

### Client

A `Client` may be connected to a few rooms on euphoria and thus manages a few
`Room` objects. It has functions for joining and leaving rooms on euphoria, and
it can also be connected to the same room multiple times (resulting in multiple
`Room` objects).

The `Client` has a few `on_<event>` functions (e. g. `on_message`, `on_join`)
that are triggered by events in any of the `Room` objects it manages. This
allows a `Client` to react to various things happening in its `Room`s.

### Bot

A `Bot` is a client that:

- is configured using a config file
- reacts to commands using a command system
- implements most commands specified in the
  [botrulez](https://github.com/jedevc/botrulez)

The config file includes the bot's default nick, initial rooms and bot-specific
configuration. Upon starting a `Bot`, it joins the rooms specified in the
config, setting its nick to the default nick.

The command system can react to general and specific commands as specified in
the botrulez, and can parse command arguments with or without bash-style string
escaping, and with or without unix-like syntax (flags and optional arguments).

### Module, ModuleBot

A `Module` is a `Bot` that can also be used as a module in a `ModuleBot`. This
is like combining multiple bots into a single bot.

The most notable differences are the new `DESCRIPTION` and `standalone` fields.
The `DESCRIPTION` field contains a short description of the module, whereas the
`standalone` field answers the question whether the `Module` is being run as
standalone bot or part of a `ModuleBot`.
