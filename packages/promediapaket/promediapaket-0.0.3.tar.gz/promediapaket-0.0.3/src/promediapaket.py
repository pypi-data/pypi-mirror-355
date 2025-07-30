from dataclasses import dataclass, asdict
from tempfile import TemporaryDirectory
from json import dumps, loads
from os import PathLike
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from typing import Self

from lib.ffmpeg import check_for_errors
from lib.zip import ZipMount
from lib.utils import log


def test_zip(zip_path: PathLike | str):
    try:
        if ZipFile(zip_path).testzip():
            log("ERROR", f"PMP not valid! {zip_path}")
            raise ValueError("PMP not valid!")

    except BadZipFile:
        log("ERROR", f"PMP not valid! {zip_path}")
        raise ValueError("PMP not valid!")


@dataclass(frozen=True, eq=True)
class VideoTypes:
    STANDARD = 0
    EPISODE = 1
    MOVIE = 0


@dataclass
class Metadata:
    version: int = 1  # Version der Datei
    video_filepath: str = "video.mkv"  # Relativer Pfad zur Videodatei
    audio_filepaths: list[str] = None  # Liste der Ton Sprachen. Muss mit den tatsächlich Sprachen im audios ordner übereinstimmen.
    subtitle_filepaths: list[str] = None  # Liste der Untertitle Sprachen. Muss mit den tatsächlich Sprachen im subtitles ordner übereinstimmen.

    provider: str | None = None  # Quelle des Videos. None für unbekannt/anders
    provider_id: str | None = None  # ID des Videos beim Provider selber.
    extras_main_id: str | None = None  # Die Provider ID des Hauptfilms, falls das aktuelle Video ein Extra ist.

    type: int = None  # Typ des Videos; 0 = None; 1 = "episode"; 2 = "movie"]
    title: str = None  # Titel des Videos
    description: str = None  # Beschreibung des Videos

    thumbnail_horizontal: str | None = None  # Pfad zum horizontalem Titelbild.
    thumbnail_vertical: str | None = None  # Pfad zum vertikalem Titelbild.

    def __init__(self):
        if self.audio_filepaths is None:
            self.audio_filepaths = []

        if self.subtitle_filepaths is None:
            self.subtitle_filepaths = []

    @property
    def valid(self) -> bool:
        if self.version != 1:
            return False

        if not self.video_filepath:
            return False

        if not isinstance(self.audio_filepaths, list):
            return False

        if not isinstance(self.subtitle_filepaths, list):
            return False

        if not isinstance(self.provider, str) and self.provider is not None:
            return False

        if not isinstance(self.provider_id, str) and self.provider is not None:
            return False

        if not isinstance(self.type, int):
            return False

        if not isinstance(self.title, str) or len(self.title) == 0:
            return False

        if not isinstance(self.description, str):
            return False

        if not isinstance(self.thumbnail_horizontal, str) and self.thumbnail_horizontal is not None:
            return False

        if not isinstance(self.thumbnail_vertical, str) and self.thumbnail_vertical is not None:
            return False

        return True

    @property
    def dict(self) -> dict:
        return asdict(self)

    @property
    def json(self) -> str:
        return dumps(self.dict)


@dataclass
class EpisodeMetadata(Metadata):
    series_title: str = None  # Titel der Serie
    series_id: str = None  # Serien ID beim Provider
    series_description: str = None  # Beschreibung der Serie
    series_thumbnail_horizontal: str | None = None  # Pfad zum horizontalem Serientitelbild.
    series_thumbnail_vertical: str | None = None  # Pfad zum vertikalem Serientitelbild.

    season_number: str = None  # Staffelnummer
    season_id: str = None  # Staffel ID beim Provider
    episode_number: str = None  # Episodennummer

    @property
    def valid(self) -> bool:
        if not isinstance(self.series_title, str) or len(self.series_title) == 0:
            return False

        if not isinstance(self.series_id, str) or len(self.series_id) == 0:
            return False

        if not isinstance(self.series_description, str):
            return False

        if not isinstance(self.series_thumbnail_horizontal, str) and self.series_thumbnail_horizontal is not None:
            return False

        if not isinstance(self.series_thumbnail_vertical, str) and self.series_thumbnail_vertical is not None:
            return False

        if not isinstance(self.season_number, str):
            return False

        if not isinstance(self.season_id, str):
            return False

        if not isinstance(self.episode_number, str):
            return False

        return super().valid


class ProMediaPaket:
    def __init__(self):
        self.metadata = Metadata()
        self.metadata.type = VideoTypes.STANDARD

        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        (self.tmp_path / "audios").mkdir()
        (self.tmp_path / "subtitles").mkdir()

        # Used for fast_open()
        self.zip_mount = None

    def change_metadata_type(self, new_type: int):
        if self.metadata.type == new_type:
            return

        if new_type == VideoTypes.EPISODE:
            self.metadata.type = new_type
            self.metadata.__class__ = EpisodeMetadata

    def add_video(self, video_path: PathLike | str) -> None:
        """
        Fügt ein Video dem PMP hinzu. Symlink bis zum Speichern.
        :param video_path:
        :return:
        """
        video_path = Path(video_path)
        (self.tmp_path / video_path.name).symlink_to(video_path.absolute())
        self.metadata.video_filepath = video_path.name

    def add_audio(self, audio_path: PathLike | str) -> None:
        """
        Fügt eine Tonspur dem PMP hinzu. Symlink bis zum Speichern.
        :param audio_path:
        :return:
        """
        audio_path = Path(audio_path)
        audio_filepath = (self.tmp_path / "audios" / audio_path.name)
        if audio_filepath.exists():
            log("INFO", f"Audio file already exists. Skipping. {audio_filepath}")
            return

        audio_filepath.symlink_to(audio_path.absolute())
        self.metadata.audio_filepaths.append(audio_path.name)

    def add_subtitle(self, subtitle_path: PathLike | str) -> None:
        """
        Fügt einen Untertitel dem PMP hinzu. Symlink bis zum Speichern.
        :param subtitle_path:
        :return:
        """
        subtitle_path = Path(subtitle_path)
        subtitle_filepath = (self.tmp_path / "subtitles" / subtitle_path.name)
        if subtitle_filepath.exists():
            log("INFO", f"Subtitle file already exists. Skipping. {subtitle_filepath}")
            return

        subtitle_filepath.symlink_to(subtitle_path.absolute())
        self.metadata.subtitle_filepaths.append(subtitle_path.name)

    def set_provider(self, provider: str | None, provider_id: str | None) -> None:
        self.metadata.provider = provider
        self.metadata.provider_id = provider_id

    def set_titel(self, title: str | None) -> None:
        self.metadata.title = title

    def set_description(self, description: str | None) -> None:
        self.metadata.description = description

    def set_thumbnail_horizontal(self, thumbnail_horizontal: PathLike | str) -> None:
        thumbnail_horizontal = Path(thumbnail_horizontal)
        if not (self.tmp_path / thumbnail_horizontal.name).is_symlink():
            (self.tmp_path / thumbnail_horizontal.name).symlink_to(thumbnail_horizontal.absolute())
        self.metadata.thumbnail_horizontal = thumbnail_horizontal.name

    def set_thumbnail_vertical(self, thumbnail_vertical: PathLike | str) -> None:
        thumbnail_vertical = Path(thumbnail_vertical)
        if not (self.tmp_path / thumbnail_vertical.name).is_symlink():
            (self.tmp_path / thumbnail_vertical.name).symlink_to(thumbnail_vertical.absolute())
        self.metadata.thumbnail_vertical = thumbnail_vertical.name

    def set_series_title(self, series_title: str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        self.metadata.series_title = series_title

    def set_series_id(self, series_id: str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        self.metadata.series_id = series_id

    def set_series_description(self, series_description: str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        self.metadata.series_description = series_description

    def set_series_thumbnail_horizontal(self, series_thumbnail_horizontal: PathLike | str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        series_thumbnail_horizontal = Path(series_thumbnail_horizontal)
        if not (self.tmp_path / series_thumbnail_horizontal.name).is_symlink():
            (self.tmp_path / series_thumbnail_horizontal.name).symlink_to(series_thumbnail_horizontal.absolute())
        self.metadata.series_thumbnail_horizontal = series_thumbnail_horizontal.name

    def set_series_thumbnail_vertical(self, series_thumbnail_vertical: PathLike | str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        series_thumbnail_vertical = Path(series_thumbnail_vertical)
        if not (self.tmp_path / series_thumbnail_vertical.name).is_symlink():
            (self.tmp_path / series_thumbnail_vertical.name).symlink_to(series_thumbnail_vertical.absolute())
        self.metadata.series_thumbnail_vertical = series_thumbnail_vertical.name

    def set_season_number(self, season_number: str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        self.metadata.season_number = season_number

    def set_season_id(self, season_id: str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        self.metadata.season_id = season_id

    def set_episode_number(self, episode_number: str) -> None:
        self.change_metadata_type(VideoTypes.EPISODE)
        self.metadata.episode_number = episode_number

    def write_metadata(self) -> None:
        (self.tmp_path / "metadata.json").write_text(self.metadata.json, "utf-8")

    def pack(self, pack_target: PathLike | str = ".") -> Path | None:
        """
        ONLY USABLE ONCE!
        Packs the PMP to a .pmp file.
        Afterword deletes the PMP Tmp Dir.
        If the PMP Target file already exists, it will be overwritten.
        :param pack_target: Output FOLDER for the file, naming is done internally.
        :return: Path to new .pmp file.
        """
        if not self.valid:
            log("ERROR", f"PMP not valid! {self.metadata.title}")
            raise RuntimeError(f"PMP not valid! {self.metadata.title}")

        self.write_metadata()

        # Make title safe for ext4 filesystem. Windows will shit itself.
        safe_title = self.metadata.title.replace('/', '⧸')
        if '/' in self.metadata.provider_id:
            log("WARN", "Slash / found in Provider Id!")
            self.metadata.provider_id = self.metadata.provider_id.replace('/', '⧸')

        pack_dir = Path(pack_target)
        pack_dir.mkdir(exist_ok=True, parents=True)
        if self.metadata.extras_main_id:
            out_file = pack_dir / f"extra@{self.metadata.provider}@{self.metadata.extras_main_id}@{self.metadata.provider_id}@{safe_title}.pmp"
        else:
            out_file = pack_dir / f"{self.metadata.provider}@{self.metadata.provider_id}@{safe_title}.pmp"

        while True:
            try:
                out_file.exists()
                break
            except OSError as exc:
                if exc.errno != 36:
                    raise exc

                log("WARN", f"Filename was to long: {out_file}")
                out_file = out_file.with_stem(out_file.stem[::-1].split(" ", 1)[-1][::-1])

        zip_target_file = out_file
        if out_file.exists():
            log("INFO", f"PMP File already exists. Overwriting: {out_file}")
            zip_target_file = out_file.with_stem(f'tmp@{self.metadata.provider}@{self.metadata.provider_id}.pmp')

        with ZipFile(zip_target_file, "w") as zipfile:
            for file in self.tmp_path.rglob('*'):
                if file.is_dir():
                    continue

                zipfile.write(file, file.relative_to(self.tmp_path))

        if test_zip(zip_target_file):
            log("ERROR", f"PMP file packing failed: {out_file}")
            zip_target_file.unlink()
            raise RuntimeError(f"PMP file packing failed: {out_file}")

        if zip_target_file != out_file:
            out_file.unlink()
            zip_target_file.rename(out_file)

        self.tmp_dir.cleanup()
        return out_file

    @classmethod
    def open(cls, path: PathLike | str) -> Self:
        self = cls.__new__(cls)
        self.__init__()

        with ZipFile(path) as zipfile:
            zipfile.extractall(self.tmp_path)

        metadata_json = loads((self.tmp_path / "metadata.json").read_text(encoding="utf-8"))
        if metadata_json['type'] != self.metadata.type:
            self.change_metadata_type(metadata_json['type'])
        self.metadata.__dict__ = metadata_json

        return self

    @classmethod
    def fast_open(cls, path: PathLike | str) -> Self:
        """
        Uses Mount-Zip to mount the Zipfile instead of extracting it all first.
        :param path:
        :return:
        """
        self = cls.__new__(cls)
        self.__init__()
        self.tmp_dir.cleanup()

        self.zip_mount = ZipMount(path)
        self.tmp_dir = self.zip_mount.tmp_dir
        self.tmp_path = self.zip_mount.tmp_path

        metadata_json = loads((self.tmp_path / "metadata.json").read_text(encoding="utf-8"))
        if metadata_json['type'] != self.metadata.type:
            self.change_metadata_type(metadata_json['type'])
        self.metadata.__dict__ = metadata_json

        return self

    @classmethod
    def metadata(cls, path: PathLike | str) -> Metadata:
        self = cls.__new__(cls)
        self.__init__()

        with ZipFile(path) as zipfile:
            zipfile.extract("metadata.json", self.tmp_path)

        metadata_json = loads((self.tmp_path / "metadata.json").read_text(encoding="utf-8"))
        if metadata_json['type'] != self.metadata.type:
            self.change_metadata_type(metadata_json['type'])
        self.metadata.__dict__ = metadata_json

        return self.metadata

    @property
    def valid(self) -> bool:
        if check_for_errors(self.tmp_path / self.metadata.video_filepath):
            return False

        if any([check_for_errors(self.tmp_path / "audios" / audio) for audio in self.metadata.audio_filepaths]):
            return False

        return self.metadata.valid
