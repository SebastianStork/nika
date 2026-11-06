"""Unit tests for install-time Docker image reconciliation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from nika.workflows.setup import images

pytestmark = pytest.mark.unit

PINNED_IMAGE = "ghcr.io/nokia/srlinux:24.10@sha256:required"
PINNED_DIGEST = "ghcr.io/nokia/srlinux@sha256:required"
STALE_DIGEST = "ghcr.io/nokia/srlinux@sha256:stale"


def _digest_only_image(ref: str) -> SimpleNamespace:
    return SimpleNamespace(tags=[ref], attrs={"RepoDigests": []}, id=f"id-{ref}")


def test_prune_keeps_required_digest_exposed_as_an_image_tag() -> None:
    client = MagicMock()
    client.images.list.side_effect = [[_digest_only_image(PINNED_DIGEST)], []]
    client.containers.list.return_value = []

    with (
        patch.object(images, "_get_client", return_value=client),
        patch.object(images, "owned_images", return_value=[PINNED_IMAGE]),
        patch.object(images, "legacy_images", return_value=[]),
    ):
        actions = images.prune_stale_images()

    assert actions == []
    client.images.remove.assert_not_called()


def test_prune_removes_unrequired_digest_exposed_as_an_image_tag() -> None:
    client = MagicMock()
    client.images.list.side_effect = [[_digest_only_image(STALE_DIGEST)], []]
    client.containers.list.return_value = []

    with (
        patch.object(images, "_get_client", return_value=client),
        patch.object(images, "owned_images", return_value=[PINNED_IMAGE]),
        patch.object(images, "legacy_images", return_value=[]),
    ):
        actions = images.prune_stale_images()

    assert actions == [f"removed stale image {STALE_DIGEST}"]
    client.images.remove.assert_called_once_with(STALE_DIGEST)
