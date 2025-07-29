# Headless playback server for Raphson Music

Client for the Raphson Music server that can be controlled remotely via a simple web interface or [Home Assistant](https://codeberg.org/raphson/music-headless-ha/).

## Installation

### Debian

Add this repository to your system: https://deb.rkslot.nl/

Then run `apt install raphson-music-headless`

### pipx

```
pipx install raphson-music-headless[mpv]
```
or
```
pipx install raphson-music-headless[vlc]
```

Run: `raphson-music-headless`

### git
Install the dependencies python3-aiohttp and python3-mpv using your distribution's package manager or using pip in a venv.

Install [music-client-python](https://codeberg.org/raphson/music-client-python) in a venv.

```
git clone https://codeberg.org/raphson/music-headless
cd music-headless
python3 -m raphson_music_headless
```


## Usage

1. Create a `config.json` file with credentials (see `config.json.example`).
2. Run `raphson-music-headless --config config.json`

By default, the program looks for a configuration file at `/etc/raphson-music-headless.json`.

## Players

Either MPV or VLC can be used as audio player backend. Respectively, `python-mpv` or `python-vlc` should be installed. Configure `player` accordingly in `config.json`.

## API

See [API.md](./docs/API.md)

## Temporary files

The server writes music to temporary files so VLC can access them. On Linux, the `/tmp` directory is used for this purpose. It is strongly recommended to mount `tmpfs` on `/tmp` to avoid unnecessary writes to your disk, especially when using a Raspberry Pi with sd card.

Check if it is the case by running `mount | grep /tmp`. It should show something like: `tmpfs on /tmp type tmpfs ...`

## Cache size

The `cache_size` setting determines the number of cached tracks for each playlist. These tracks are kept in memory, consuming roughly 3 - 6MB per track including cover image. Say `cache_size` is set to 4 and you use a maximum of 10 playlists, you will need around 200MiB of memory.

## Bugs

When playing mono audio (like news), sound may only be played on the left channel. This appears to be an issue with PipeWire.
