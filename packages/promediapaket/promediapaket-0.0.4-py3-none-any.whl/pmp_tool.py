from sys import argv

from promediapaket import ProMediaPaket


if __name__ == '__main__':
    if len(argv) != 5:
        print('Usage: pmp_tool.py <command> <command_option> <pmp_file> <file>')
        print('Commands: add, remove, convert')
        print('Command Option: video, audio, subtitle, thumnail_horizontal, thumbnail_vertical, series_thumbnail_horizontal, series_thumbnail_vertical')
        print('Command Option for convert: tomp4, frommp4')
        exit(1)

    pmp = ProMediaPaket.fast_open(argv[3])

    if argv[1] == 'add':
        if argv[2] == 'video':
            pmp.add_video(argv[4])

        if argv[2] == 'audio':
            pmp.add_audio(argv[4])

        if argv[2] == 'subtitle':
            pmp.add_subtitle(argv[4])

        if argv[2] == 'thumnail_horizontal':
            pmp.set_thumbnail_horizontal(argv[4])

        if argv[2] == 'thumbnail_vertical':
            pmp.set_thumbnail_vertical(argv[4])

        if argv[2] == 'series_thumbnail_horizontal':
            pmp.set_series_thumbnail_horizontal(argv[4])

        if argv[2] == 'series_thumbnail_vertical':
            pmp.set_series_thumbnail_vertical(argv[4])

        pmp.pack(argv[3])

    if argv[1] == 'remove':
        if argv[2] == 'video':
            print("The Video can't be removed")
            raise ValueError("The Video can't be removed")

        if argv[2] == 'audio':
            pmp.metadata.audio_filepaths.remove(argv[4])

        if argv[2] == 'subtitle':
            pmp.metadata.subtitle_filepaths.remove(argv[4])

        if argv[2] == 'thumnail_horizontal':
            pmp.metadata.thumbnail_horizontal = None

        if argv[2] == 'thumbnail_vertical':
            pmp.metadata.thumbnail_vertical = None

        if argv[2] == 'series_thumbnail_horizontal':
            pmp.metadata.series_thumbnail_horizontal = None

        if argv[2] == 'series_thumbnail_vertical':
            pmp.metadata.series_thumbnail_vertical = None

        pmp.pack(argv[3])

    if argv[1] == 'convert':
        if argv[2] == 'tomp4':
            raise NotImplementedError

        if argv[2] == 'frommp4':
            raise NotImplementedError
