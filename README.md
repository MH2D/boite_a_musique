# Boite a Musique

Scan a barcode portrait, hear the person's song. Runs headlessly on a Raspberry Pi 2 Model B.

## Raspberry Pi connection

- **IP**: `192.168.1.51` (Ethernet, may change after router reboot)
- **User**: `ugo`
- **Password**: `kfarfila`
- **OS**: Raspberry Pi OS with Desktop (Bookworm, 32-bit)

```bash
# Connect
sshpass -p "kfarfila" ssh ugo@192.168.1.51

# If IP changed, find the Pi by its MAC address (b8:27:eb)
ping -c 3 224.0.0.1 && arp -a | grep "b8:27:eb"
```

## Hardware setup

- **Barcode scanner** -> USB port on the Pi (detected as "USB Keyboard", vendor 0x0808)
- **Speaker/headphones** -> 3.5mm audio jack on the Pi
- **Power** -> micro-USB
- **Network** -> Ethernet cable (Pi 2 has no built-in Wi-Fi)

## How it works

1. The `boite-a-musique` systemd service starts automatically on boot
2. The scanner reads barcodes via evdev (raw USB input, no keyboard layout dependency)
3. The barcode (e.g. `IAL0016`) is looked up in `mappings.json`
4. If found, the mapped song plays through `mpv` on the 3.5mm jack
5. Scanning a new barcode stops the current song and starts the new one

## Useful commands

```bash
PI="sshpass -p kfarfila ssh ugo@192.168.1.51"

# Check service status
$PI "sudo systemctl status boite-a-musique"

# View live logs
$PI "sudo journalctl -u boite-a-musique -f --no-pager"

# View recent logs
$PI "sudo journalctl -u boite-a-musique -n 30 --no-pager"

# Restart the service
$PI "sudo systemctl restart boite-a-musique"

# Stop the service
$PI "sudo systemctl stop boite-a-musique"

# Test audio manually
$PI "mpv --no-video --audio-device=alsa/plughw:Headphones,0 --length=5 ~/boite_a_musique/musique_portrait/Canopee.mp3"
```

## Files on the Raspberry Pi

Location: `/home/ugo/boite_a_musique/`

```
boite_a_musique/
  mappings.json              # barcode -> {name, song} mappings
  data.json                  # original photo -> song list
  musique_portrait/          # 33 MP3/M4A song files
  portraits/                 # portrait photos
  barcodes/                  # barcode PNG images
  barcodes_print_sheet.pdf   # printable barcode sheet
  src/i_am_listening/        # Python source
    __main__.py              # entry point
    cli.py                   # CLI commands (play, add, list, remove)
    config.py                # paths + platform audio config
    scanner.py               # evdev barcode reader (USB HID)
    player.py                # mpv subprocess wrapper
    mappings.py              # mappings.json read/write
```

Systemd service: `/etc/systemd/system/boite-a-musique.service`

## Updating code on the Pi

After editing files locally, push them:

```bash
sshpass -p "kfarfila" scp -r src/i_am_listening/ ugo@192.168.1.51:~/boite_a_musique/src/i_am_listening/
sshpass -p "kfarfila" ssh ugo@192.168.1.51 "sudo systemctl restart boite-a-musique"
```

## Running locally (Mac)

On macOS, the scanner acts as a keyboard (stdin) and audio plays via `afplay`:

```bash
uv run python -m i_am_listening play
```
