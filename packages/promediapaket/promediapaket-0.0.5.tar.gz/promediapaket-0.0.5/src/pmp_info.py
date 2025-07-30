from sys import argv

from promediapaket import ProMediaPaket, EpisodeMetadata

if __name__ == '__main__':
    if len(argv) != 2:
        print('Usage: pmp_info.py <file>')
        exit(1)

    print("File: ", argv[1])
    pmp_metadata = ProMediaPaket.metadata(argv[1])
    print("Version: ", pmp_metadata.version)
    print("Video-Pfad: ", pmp_metadata.video_filepath)
    print("Audio-Pfade: ", pmp_metadata.audio_filepaths)
    print("Untertitel-Pfade: ", pmp_metadata.subtitle_filepaths)

    print("Provider: ", pmp_metadata.provider)
    print("Provider-ID: ", pmp_metadata.provider_id)
    print("Extras Main-ID: ", pmp_metadata.extras_main_id)

    print("Typ: ", pmp_metadata.type)
    print("Titel: ", pmp_metadata.title)
    print("Beschreibung: ", pmp_metadata.description)

    print("Thumbnail horizontal: ", pmp_metadata.thumbnail_horizontal)
    print("Thumbnail vertikal: ", pmp_metadata.thumbnail_vertical)

    if isinstance(pmp_metadata, EpisodeMetadata):
        print("Serien-Titel: ", pmp_metadata.series_title)
        print("Serien-ID: ", pmp_metadata.series_id)
        print("Serien-Beschreibung: ", pmp_metadata.series_description)
        print("Serien-Thumbnail horizontal: ", pmp_metadata.series_thumbnail_horizontal)
        print("Serien-Thumbnail vertikal: ", pmp_metadata.series_thumbnail_vertical)

        print("Staffelnummer: ", pmp_metadata.season_number)
        print("Staffel-ID: ", pmp_metadata.season_id)
        print("Episodennummer: ", pmp_metadata.episode_number)
