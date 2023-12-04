# homeassistant-trakt

This custom component for Home Assistant allows you to integrate your [Trakt](https://trakt.tv) now playing status as a sensor.

## Installation

Use [HACS](https://hacs.xyz) or manually installed the files into your `config/custom_components/` directory.

```sh
$ ssh homeassistant
$ cd /config/custom_components/
$ curl -L https://github.com/josh/homeassistant-trakt/archive/refs/heads/main.tar.gz |
    tar -xz --strip-components=2 homeassistant-trakt-main/custom_components/trakt
```
