from devpi_common.archive import zip_dict
from devpi_common.metadata import parse_version
from devpi_web.indexing import ProjectIndexingInfo
from devpi_web.indexing import iter_projects
from devpi_web.indexing import preprocess_project
from devpi_server import __version__ as _devpi_server_version
import pytest


devpi_server_version = parse_version(_devpi_server_version)
pytestmark = [pytest.mark.notransaction]


@pytest.mark.skipif(
    devpi_server_version < parse_version("6.6.0dev"),
    reason="Needs un-normalized project names from list_projects_perstage on mirrors")
def test_original_project_name(pypistage):
    xom = pypistage.xom
    projects = set(["Django", "pytest", "ploy_ansible"])
    result = set()
    with xom.keyfs.read_transaction():
        pypistage.mock_simple_projects(projects)
        for project in iter_projects(xom):
            data = preprocess_project(project)
            result.add(data['name'])
    assert result == projects


def test_inheritance(xom):
    with xom.keyfs.write_transaction():
        user = xom.model.create_user("one", "one")
        prod = user.create_stage("prod")
        prod.set_versiondata({"name": "proj", "version": "1.0"})
        dev = user.create_stage("dev", bases=(prod.name,))
        dev.set_versiondata({"name": "proj", "version": "1.1"})

    with xom.keyfs.read_transaction():
        stage = xom.model.getstage(dev.name)
        preprocess_project(ProjectIndexingInfo(stage=stage, name="proj"))


@pytest.mark.with_notifier
def test_doc_unpack_cleanup(mapp, testapp):
    from devpi_web.doczip import get_unpack_path
    api = mapp.create_and_use()
    content = zip_dict({
        "index.html": "<html><body>2.6</body></html>",
        "foo.html": "<html><body>Foo</body></html>"})
    mapp.set_versiondata({"name": "pkg1", "version": "2.6"})
    mapp.upload_doc("pkg1.zip", content, "pkg1", "2.6", code=200,
                    waithooks=True)
    with mapp.xom.keyfs.read_transaction():
        stage = mapp.xom.model.getstage(api.stagename)
        path = get_unpack_path(stage, 'pkg1', '2.6')
    testapp.xget(200, api.index + '/pkg1/2.6/+doc/foo.html')
    assert path.joinpath("foo.html").exists()
    content = zip_dict({
        "index.html": "<html><body>2.6</body></html>"})
    mapp.upload_doc("pkg1.zip", content, "pkg1", "2.6", code=200,
                    waithooks=True)
    with mapp.xom.keyfs.read_transaction():
        stage = mapp.xom.model.getstage(api.stagename)
        path = get_unpack_path(stage, 'pkg1', '2.6')
    testapp.xget(404, api.index + '/pkg1/2.6/+doc/foo.html')
    assert not path.joinpath("foo.html").exists()


@pytest.mark.with_notifier
def test_doc_unpack_hash_mismatch(caplog, mapp):
    from devpi_web.doczip import get_unpack_path
    from devpi_web.doczip import locked_unpack_path
    from devpi_web.doczip import unpack_docs
    api = mapp.create_and_use()
    content = zip_dict({
        "index.html": "<html><body>2.6</body></html>"})
    mapp.set_versiondata({"name": "pkg1", "version": "2.6"})
    mapp.upload_doc("pkg1.zip", content, "pkg1", "2.6", code=200,
                    waithooks=True)
    with mapp.xom.keyfs.read_transaction():
        stage = mapp.xom.model.getstage(api.stagename)
        linkstore = stage.get_linkstore_perstage("pkg1", "2.6")
        (link,) = linkstore.get_links(rel='doczip')
        path = unpack_docs(stage, 'pkg1', '2.6', link.entry)
    assert path.exists()
    # make sure there is a path that is not existing in the zip,
    # so we can test for its removal
    foo_path = path.joinpath("foo.html")
    assert not foo_path.exists()
    foo_path.touch()
    assert foo_path.exists()
    with mapp.xom.keyfs.read_transaction():
        # now mess with the hash file and make it bigger than the hash_spec,
        # as there was a problem with writing the file correctly before
        bad_hash = "foo" * 300
        with locked_unpack_path(stage, "pkg1", "2.6") as (hash_file, _unpack_path):
            hash_file.seek(0)
            hash_file.write(bad_hash)
        hash_path = get_unpack_path(stage, "pkg1", "2.6").with_suffix(".hash")
        # make sure it is set correctly to the bad value
        assert hash_path.read_text() == bad_hash
        stage = mapp.xom.model.getstage(api.stagename)
        linkstore = stage.get_linkstore_perstage("pkg1", "2.6")
        (link,) = linkstore.get_links(rel='doczip')
        caplog.clear()
        unpack_docs(stage, 'pkg1', '2.6', link.entry)
        assert len(caplog.getrecords("unpacked")) == 1
        assert hash_path.read_text() == link.entry.best_available_hash_spec
        # unpack again
        new_path = unpack_docs(stage, 'pkg1', '2.6', link.entry)
        assert len(caplog.getrecords("unpacked")) == 1
        assert new_path == path
        assert new_path.exists()
        assert "2.6" in new_path.joinpath("index.html").read_text()
        # the hash was written more than once
        assert new_path.with_suffix(".hash").read_text() == link.entry.best_available_hash_spec
    assert not foo_path.exists()


@pytest.mark.with_notifier
def test_empty_doczip(mapp):
    from devpi_server.filestore import get_hashes
    from devpi_web.doczip import Docs
    from devpi_web.doczip import remove_docs
    from devpi_web.doczip import unpack_docs
    api = mapp.create_and_use()
    empty_doczip = b'PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    empty_doczip_hash_spec = get_hashes(empty_doczip).get_default_spec()
    mapp.set_versiondata({"name": "pkg1", "version": "2.6"})
    mapp.upload_doc("pkg1.zip", empty_doczip, "pkg1", "2.6", code=200,
                    waithooks=True)
    (name, version) = ('pkg1', '2.6')
    with mapp.xom.keyfs.read_transaction():
        stage = mapp.xom.model.getstage(api.stagename)
        linkstore = stage.get_linkstore_perstage(name, version)
        (link,) = linkstore.get_links(rel='doczip')
        path = unpack_docs(stage, name, version, link.entry)
    assert not path.exists()
    assert path.with_suffix(".hash").exists()
    assert path.with_suffix(".hash").read_text() == empty_doczip_hash_spec
    with mapp.xom.keyfs.read_transaction():
        stage = mapp.xom.model.getstage(api.stagename)
        assert list(Docs(stage, name, version).items()) == []
    with mapp.xom.keyfs.read_transaction():
        stage = mapp.xom.model.getstage(api.stagename)
        remove_docs(stage, name, version)
    # the hash file should be removed
    assert not path.with_suffix(".hash").exists()
