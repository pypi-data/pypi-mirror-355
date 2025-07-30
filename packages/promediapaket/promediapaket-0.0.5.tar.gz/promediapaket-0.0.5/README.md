# ProMediaPaket

ProMediaPaket (PMP) ist ein Dateiformatstandard und eine Bibliothek zur Verwaltung von Mediendateien. Es bietet eine einheitliche Möglichkeit, Video-, Audio- und Untertiteldateien in verschiedenen Sprachen zusammen mit Metadaten zu bündeln.

## Installation
```bash
pip install promediapaket
```

## Funktionen

### PMP-Dateien erstellen

Mit der `ProMediaPaket`-Klasse können Sie PMP-Dateien erstellen und verwalten:

```python
from promediapaket import ProMediaPaket

# Neue PMP-Datei erstellen
pmp = ProMediaPaket()

# Film-Metadaten festlegen
# provider ist die Quelle des Videos, z. B. zdf
# provider_id ist die Id des Videos welche die Quelle intern benutzt.
pmp.set_provider("provider", "provider_id")
pmp.set_titel("Film Titel")
pmp.add_video("pfad/zum/video.mp4")
pmp.add_audio("pfad/zur/de.mp3")
pmp.add_subtitle("pfad/zum/de.srt")
pmp.add_subtitle("pfad/zum/forced@de.srt")

# PMP-Datei speichern, nur Ordner angeben.
pmp.pack("/pafd/zur/ausgabe/")
```

### PMP-Dateien öffnen und abspielen

Zum Öffnen und Abspielen von PMP-Dateien können Sie den integrierten Player verwenden:

```bash
python player.py meine_datei.pmp
```

Der Player nutzt MPV zum Abspielen der Mediendateien mit den enthaltenen Audio- und Untertitelspuren.

### Informationen zu PMP-Dateien anzeigen

Um Informationen über eine PMP-Datei anzuzeigen:

```bash
python pmp_info.py meine_datei.pmp
```

### PMP-Dateien bearbeiten

Mit dem PMP-Tool können Sie bestehende PMP-Dateien bearbeiten:

```bash
python pmp_tool.py add audio meine_datei.pmp pfad/zur/neuen_audio.mp3
```

## PMP-Dateiformat

PMP-Dateien sind im Grunde umbenannte ZIP-Archive mit einer definierten Struktur. Details zum Format finden Sie in der [PROMEDIAPAKET.md](PROMEDIAPAKET.md) Dokumentation.

## Lizenz

Diese Software wird unter der MIT-Lizenz veröffentlicht.

