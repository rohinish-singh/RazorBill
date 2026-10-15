import os
import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.database import init_db
    from backend.src.main import (
        ALLOWED_IMAGE_EXTENSIONS,
        app,
        get_db_path,
        get_frames_dir,
        resolve_evidence_path,
    )
except ModuleNotFoundError:
    from src.database import init_db
    from src.main import (
        ALLOWED_IMAGE_EXTENSIONS,
        app,
        get_db_path,
        get_frames_dir,
        resolve_evidence_path,
    )


@pytest.fixture
def evidence_setup(tmp_path):
    test_db = str(tmp_path / "test_evidence.db")
    init_db(test_db)
    frames_dir = tmp_path / "data" / "frames"
    cam_dir = frames_dir / "CAM_01"
    nested_dir = cam_dir / "sub" / "deep"
    nested_dir.mkdir(parents=True, exist_ok=True)

    # Standard valid image
    image_content = b"\xff\xd8\xff\xe0\x00\x10JFIFfakejpegdata"
    image_file = cam_dir / "evt_unique_id.jpg"
    image_file.write_bytes(image_content)

    # Nested valid image
    nested_png_content = b"\x89PNG\r\n\x1a\nfakepngdata"
    nested_image_file = nested_dir / "nested_evt.png"
    nested_image_file.write_bytes(nested_png_content)

    # Non-image file inside frames directory
    txt_file = cam_dir / "secret.txt"
    txt_file.write_text("classified text content")

    # Target outside file in isolated tmp directory (never real system files)
    outside_file = tmp_path / "outside_secret.jpg"
    outside_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIFoutsidedata")

    app.dependency_overrides[get_db_path] = lambda: test_db
    app.dependency_overrides[get_frames_dir] = lambda: str(frames_dir)

    with TestClient(app) as test_client:
        yield test_client, frames_dir, image_content, nested_png_content, outside_file

    app.dependency_overrides.clear()


def test_get_existing_evidence_image_success(evidence_setup):
    """Test retrieving existing evidence images via /data/frames and /api/evidence with varied prefixes."""
    client, _, expected_bytes, nested_bytes, _ = evidence_setup

    # 1. Via /data/frames/CAM_01/evt_unique_id.jpg
    res1 = client.get("/data/frames/CAM_01/evt_unique_id.jpg")
    assert res1.status_code == 200
    assert res1.content == expected_bytes
    assert "image/jpeg" in res1.headers.get("content-type", "")

    # 2. Via /api/evidence/CAM_01/evt_unique_id.jpg
    res2 = client.get("/api/evidence/CAM_01/evt_unique_id.jpg")
    assert res2.status_code == 200
    assert res2.content == expected_bytes
    assert "image/jpeg" in res2.headers.get("content-type", "")

    # 3. With leading 'data/frames/' prefix preserved in route
    res3 = client.get("/data/frames/data/frames/CAM_01/evt_unique_id.jpg")
    assert res3.status_code == 200
    assert res3.content == expected_bytes

    res3_api = client.get("/api/evidence/data/frames/CAM_01/evt_unique_id.jpg")
    assert res3_api.status_code == 200
    assert res3_api.content == expected_bytes

    # 4. With leading 'frames/' prefix
    res4 = client.get("/data/frames/frames/CAM_01/evt_unique_id.jpg")
    assert res4.status_code == 200
    assert res4.content == expected_bytes

    # 5. Nested paths under frames directory
    res5 = client.get("/data/frames/CAM_01/sub/deep/nested_evt.png")
    assert res5.status_code == 200
    assert res5.content == nested_bytes
    assert "image/png" in res5.headers.get("content-type", "")

    res5_api = client.get("/api/evidence/CAM_01/sub/deep/nested_evt.png")
    assert res5_api.status_code == 200
    assert res5_api.content == nested_bytes


def test_get_missing_evidence_image_returns_404(evidence_setup):
    """Test that requesting nonexistent frames returns HTTP 404 with standard message."""
    client, _, _, _, _ = evidence_setup

    res1 = client.get("/data/frames/CAM_01/missing_frame.jpg")
    assert res1.status_code == 404
    assert res1.json()["detail"] == "Evidence frame not found"

    res2 = client.get("/api/evidence/CAM_99/not_there.png")
    assert res2.status_code == 404
    assert res2.json()["detail"] == "Evidence frame not found"


def test_path_traversal_attempts_blocked_returns_404(evidence_setup):
    """Test that all path traversal attempts outside frames directory return HTTP 404."""
    client, frames_dir, _, _, outside_file = evidence_setup

    # Relative dot-dot traversal
    res1 = client.get("/data/frames/../../outside_secret.jpg")
    assert res1.status_code == 404

    res1_api = client.get("/api/evidence/../../outside_secret.jpg")
    assert res1_api.status_code == 404

    # URL-encoded traversal (%2f and %2e)
    res2 = client.get("/data/frames/..%2f..%2foutside_secret.jpg")
    assert res2.status_code == 404

    res2_encoded_dots = client.get("/data/frames/%2e%2e%2f%2e%2e%2foutside_secret.jpg")
    assert res2_encoded_dots.status_code == 404

    # Backslash traversal
    res3 = client.get("/data/frames/..\\..\\outside_secret.jpg")
    assert res3.status_code == 404

    res3_api = client.get("/api/evidence/..\\..\\outside_secret.jpg")
    assert res3_api.status_code == 404

    # Repeated separators
    res4 = client.get("/data/frames//..//..//outside_secret.jpg")
    assert res4.status_code == 404

    # Absolute path attempts via resolver function
    with pytest.raises(Exception) as excinfo:
        resolve_evidence_path(str(outside_file), base_dir=str(frames_dir))
    assert excinfo.value.status_code == 404


def test_repeated_separators_in_legitimate_path_resolves_successfully(evidence_setup):
    """Test that repeated separators in legitimate paths are collapsed safely."""
    client, _, expected_bytes, _, _ = evidence_setup

    res = client.get("/data/frames//CAM_01///evt_unique_id.jpg")
    assert res.status_code == 200
    assert res.content == expected_bytes


def test_symlink_pointing_outside_frames_dir_rejected(evidence_setup):
    """Audit 2: Test that symlinks pointing outside the frames directory are strictly rejected."""
    client, frames_dir, _, _, outside_file = evidence_setup
    cam_dir = frames_dir / "CAM_01"

    # Create a symlink inside frames_dir pointing to a file outside frames_dir
    symlink_outside = cam_dir / "symlink_outside.jpg"
    symlink_outside.symlink_to(outside_file)

    res1 = client.get("/data/frames/CAM_01/symlink_outside.jpg")
    assert res1.status_code == 404
    assert res1.json()["detail"] == "Evidence frame not found"

    res2 = client.get("/api/evidence/CAM_01/symlink_outside.jpg")
    assert res2.status_code == 404
    assert res2.json()["detail"] == "Evidence frame not found"


def test_symlink_pointing_inside_frames_dir_allowed(evidence_setup):
    """Audit 2: Test that symlinks within the frames directory pointing to valid images resolve safely."""
    client, frames_dir, expected_bytes, _, _ = evidence_setup
    cam_dir = frames_dir / "CAM_01"

    # Symlink targeting another legitimate image inside frames_dir
    target_img = cam_dir / "evt_unique_id.jpg"
    symlink_inside = cam_dir / "symlink_inside.jpg"
    symlink_inside.symlink_to(target_img)

    res1 = client.get("/data/frames/CAM_01/symlink_inside.jpg")
    assert res1.status_code == 200
    assert res1.content == expected_bytes

    res2 = client.get("/api/evidence/CAM_01/symlink_inside.jpg")
    assert res2.status_code == 200
    assert res2.content == expected_bytes


def test_symlink_targeting_non_image_file_rejected(evidence_setup):
    """Audit 2: Test that symlinks with image extension targeting non-image files are rejected."""
    client, frames_dir, _, _, _ = evidence_setup
    cam_dir = frames_dir / "CAM_01"

    # Symlink has .jpg extension but points to secret.txt
    txt_file = cam_dir / "secret.txt"
    sneaky_symlink = cam_dir / "sneaky_txt.jpg"
    sneaky_symlink.symlink_to(txt_file)

    res = client.get("/data/frames/CAM_01/sneaky_txt.jpg")
    assert res.status_code == 404
    assert res.json()["detail"] == "Evidence frame not found"


def test_disallowed_extension_returns_404(evidence_setup):
    """Test that requesting non-image files directly returns HTTP 404."""
    client, frames_dir, _, _, _ = evidence_setup
    cam_dir = frames_dir / "CAM_01"

    # Text file
    res1 = client.get("/data/frames/CAM_01/secret.txt")
    assert res1.status_code == 404
    assert res1.json()["detail"] == "Evidence frame not found"

    # Executable / script file
    script_file = cam_dir / "exploit.sh"
    script_file.write_text("#!/bin/sh\necho hi")
    res2 = client.get("/data/frames/CAM_01/exploit.sh")
    assert res2.status_code == 404

    # File with no extension
    no_ext = cam_dir / "noext"
    no_ext.write_text("data")
    res3 = client.get("/data/frames/CAM_01/noext")
    assert res3.status_code == 404
