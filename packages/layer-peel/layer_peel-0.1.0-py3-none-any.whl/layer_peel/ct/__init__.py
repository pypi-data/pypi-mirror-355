from .py7z import stream_un7z, is_7z_file
from .tgz import stream_untgz, is_tgz_file
from .tar import stream_untar, is_tar_file
from .zip import stream_unzip, is_zip_file
from .rar import stream_unrar, is_rar_file

extract_funcs = {
    is_zip_file: stream_unzip,
    is_tar_file: stream_untar,
    is_tgz_file: stream_untgz,
    is_7z_file: stream_un7z,
    is_rar_file: stream_unrar,
}
