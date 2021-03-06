import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Generator

import pytest
import vcr  # type: ignore[import]
import srt  # type: ignore[import]

from url_metadata.core import URLMetadataCache, Metadata
from url_metadata.cache import DirCache
from url_metadata.sites.youtube import get_yt_video_id


@pytest.fixture()
def ucache() -> Generator[URLMetadataCache, None, None]:  # type: ignore[misc]
    d: str = tempfile.mkdtemp()
    yield URLMetadataCache(cache_dir=d, sleep_time=0)
    shutil.rmtree(d)


# links to use; requests are cached in ./vcr/
youtube_with_cc = "https://www.youtube.com/watch?v=KXJSjte_OAI"
youtube_with_cc_skip_subs = "https://www.youtube.com/watch?v=1n3NJdqzLNg"
youtube_without_cc = "https://youtu.be/xvQUiX26RfE"
github_home = "https://github.com"
image_file = "https://i.picsum.photos/id/1000/367/267.jpg?hmac=uO9iQNujyGpqk0Ieytv_xfwbpy3ENW4PhnIZ1gsnldI"

tests_dir = os.path.dirname(os.path.abspath(__file__))


@vcr.use_cassette(os.path.join(tests_dir, "vcr/youtube_subs.yaml"))  # type: ignore
def test_youtube_has_subtitles(ucache: URLMetadataCache) -> None:

    # make sure subtitles download to file
    assert not ucache.in_cache(youtube_with_cc)
    meta_resp = ucache.get(youtube_with_cc)
    assert ucache.in_cache(youtube_with_cc)
    assert isinstance(meta_resp, Metadata)
    assert meta_resp is not None
    assert "trade-off between space" in srt.compose(meta_resp.subtitles)

    # make sure corresponding file exists
    dcache = ucache.metadata_cache.dir_cache
    assert isinstance(dcache, DirCache)
    dir_full_path = dcache.get(ucache.preprocess_url(youtube_with_cc))
    assert dir_full_path.endswith("data/2/c/7/6284b2f664f381372fab3276449b2/000")

    subtitles_file = Path(os.path.join(dir_full_path, "subtitles.srt"))
    assert subtitles_file.exists()

    # make sure subtitle is in cache dir
    assert "trade-off between space" in subtitles_file.read_text()


def test_youtube_preprocessor(ucache: URLMetadataCache) -> None:
    assert youtube_without_cc != "https://www.youtube.com/watch?v=xvQUiX26RfE"
    assert (
        ucache.preprocess_url(youtube_without_cc)
        == "https://www.youtube.com/watch?v=xvQUiX26RfE"
    )


@vcr.use_cassette(os.path.join(tests_dir, "vcr/youtube_no_subs.yaml"))  # type: ignore
def test_doesnt_have_subtitles(ucache: URLMetadataCache) -> None:
    meta_resp = ucache.get(youtube_without_cc)
    # shouldnt match, is the 'corrected' preprocessed URL
    assert meta_resp.url != youtube_without_cc
    # make sure this parsed the youtube id
    assert "xvQUiX26RfE" == get_yt_video_id(youtube_without_cc)
    assert meta_resp.subtitles is None
    dir_full_path = ucache.metadata_cache.dir_cache.get(
        ucache.preprocess_url(youtube_without_cc)
    )
    assert not os.path.exists(os.path.join(dir_full_path, "subtitles.srt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))
    # this deletes the summary files on purpose, since theyre somewhat useless
    assert not os.path.exists(os.path.join(dir_full_path, "summary.html"))
    assert not os.path.exists(os.path.join(dir_full_path, "summary.txt"))


skip_dl_fp = os.path.join(tests_dir, "vcr/skip_downloading_youtube_subtitles.yaml")


@vcr.use_cassette(skip_dl_fp)  # type: ignore
def test_skip_downloading_youtube_subtitles(ucache: URLMetadataCache) -> None:

    # see if this URL would succeed usually, download subtitles
    assert not ucache.in_cache(youtube_with_cc_skip_subs)
    meta_resp = ucache.get(youtube_with_cc_skip_subs)
    assert meta_resp is not None
    assert ucache.in_cache(youtube_with_cc_skip_subs)
    assert meta_resp is not None
    assert "coda radio" in srt.compose(meta_resp.subtitles).casefold()
    dir_full_path = ucache.metadata_cache.dir_cache.get(youtube_with_cc_skip_subs)

    # delete, and check its deleted
    shutil.rmtree(dir_full_path)
    assert not ucache.in_cache(youtube_with_cc_skip_subs)

    # this is just set in __init__, is the same
    ucache.skip_subtitles = True

    # make sure we didnt get any subtitles
    meta_resp = ucache.get(youtube_with_cc_skip_subs)
    assert meta_resp.subtitles is None


@vcr.use_cassette(os.path.join(tests_dir, "vcr/generic_url.yaml"))  # type: ignore
def test_generic_url(ucache: URLMetadataCache) -> None:
    meta_resp = ucache.get(github_home)  # type: ignore[union-attr]
    assert ucache.in_cache(github_home)

    # basic tests for any sort of text-based URL
    assert meta_resp.html_summary is not None
    assert isinstance(meta_resp.timestamp, datetime)
    assert meta_resp.subtitles is None
    assert meta_resp.info["title"].casefold().startswith("github")

    dir_full_path = ucache.metadata_cache.dir_cache.get(github_home)
    # make sure subtitles file doesn't exist for item which doesnt have subtitle
    assert not os.path.exists(os.path.join(dir_full_path, "subtitles.srt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))


@vcr.use_cassette(os.path.join(tests_dir, "vcr/test_image.yaml"))  # type: ignore
def test_image(ucache: URLMetadataCache) -> None:

    meta_resp = ucache.get(image_file)
    assert ucache.in_cache(image_file)

    # assert Metadata values
    assert meta_resp.html_summary is None
    assert meta_resp.subtitles is None
    imgs: List[Dict[str, Any]] = meta_resp.info["images"]
    assert len(imgs) == 1
    assert imgs[0]["type"] == "body_image"
    assert imgs[0]["src"].startswith("https://i.picsum.photos/id/")

    # make sure expected files exist/dont exist
    dir_full_path = ucache.metadata_cache.dir_cache.get(image_file)
    assert not os.path.exists(os.path.join(dir_full_path, "subtitles.srt"))
    assert not os.path.exists(os.path.join(dir_full_path, "summary.html"))
    assert not os.path.exists(os.path.join(dir_full_path, "summary.txt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))
