import json

from battery_frontier.partners.dossiers import write_partner_dossiers


def test_partner_dossiers_write_latest_and_archive_on_first_run(tmp_path) -> None:
    manifest_path, archive_dir = write_partner_dossiers(output_dir=tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert archive_dir is not None
    assert archive_dir.exists()
    assert manifest["dossier_count"] == 5
    assert manifest["archive_created"] is True
    assert manifest["input_signature_sha256"]
    assert "plane_manufacturer_dossier" in manifest["written_artifacts"]
    assert (tmp_path / "latest" / "plane_manufacturer_dossier.md").exists()


def test_partner_dossiers_skip_archive_without_significant_input_change(tmp_path) -> None:
    write_partner_dossiers(output_dir=tmp_path)
    _, second_archive = write_partner_dossiers(output_dir=tmp_path)

    assert second_archive is None
