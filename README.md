![worblehat](worblehat.png)

# 👉👁️👄👁️👈

# Worblehat

More information on  <https://www.pvv.ntnu.no/pvv/Bokhyllen/Worblehat/>

## What?

Worblehat is a simple library management system written specifically for Programvareverkstedet.

## Why?

Programvareverkstedet is a small community with many books and games. A simple web platform is needed to manage the library. We need to know who owns each item, if we can loan it out and where it is.

Programvareverkstedet har en rekke bøker, og en konstant tilstrøm av nye.
Teoretisk sett skal disse ryddes og kategoriseres jevntlig, men da dette ikke gjøres ofte nok kan det være et varig strev å finne ut hvor bøker står til enhver tid.
Styret har derfor tatt initiativ til å opprette et biblioteksystem for å systematisere bøkene.
Prosjektet har fått navn Worblehat etter en bibliotekar i Terry Pratchetts discworld serie.
Worblehatt har vært påbegynnt flere ganger opp gjennom historien uten å komme i noen form for funksjonell tilstand enda.

# Technical details

## Setup

This project uses `uv` as its buildtool as of February 2025.

```console
$ uv run alembic -x config=./config-template.toml upgrade head
$ uv run worblehat -c config-template.toml devscripts seed-test-data
$ uv run worblehat --help
$ uv run worblehat -c config-template.toml cli
```

## How to configure

See `config.template` for configurable settings.

Unless provided through the `--config` flag, program will automatically look for a config file in these locations:

- `./config.toml`
- `~/.config/worblehat/config.toml`
- `/var/lib/worblehat/config.toml`

Run `uv run worblehat --help` for more info
