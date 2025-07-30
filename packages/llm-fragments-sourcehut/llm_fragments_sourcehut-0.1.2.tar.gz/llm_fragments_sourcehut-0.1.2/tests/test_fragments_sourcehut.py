from llm_fragments_sourcehut import srht_loader
import pytest


@pytest.mark.parametrize(
    "argument",
    ("~amolith/adresilo-server",),
)
def test_srht_loader(argument):
    fragments = srht_loader(argument)
    by_source = {
        fragment.source.replace("\\", "/").split("/", 1)[1]: str(fragment)
        for fragment in fragments
    }

    # Check for a few key files. Their content may change, so we check for presence and start.
    assert "adresilo-server/README.md" in by_source
    assert by_source["adresilo-server/README.md"].startswith("<!--")

    assert "adresilo-server/main.go" in by_source
    assert by_source["adresilo-server/main.go"].strip().startswith("//")

    # Test error cases
    with pytest.raises(ValueError) as ex:
        srht_loader("~amolith/nonexistent-repo")
    assert "Failed to clone repository" in str(ex.value)
