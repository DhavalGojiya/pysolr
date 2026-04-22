import contextlib

import pytest

from pysolr import SolrCoreAdmin, SolrError, SolrNodeAdmin


class TestSolrCoreAdmin:
    """Test the SolrCoreAdmin class."""

    @classmethod
    def setup_class(cls):
        """
        Initialize a shared SolrCoreAdmin instance for all test methods.
        """
        cls.solr_admin = SolrCoreAdmin("http://localhost:8983/solr/admin/cores")

    def setup_method(self):
        """
        Ensure no leftover demo cores before each test.
        """
        self._unload_demo_cores()

    def _unload_demo_cores(self):
        """
        Unload any demo cores left over from previous test runs.

        Solr keeps core state between requests, unlike a test database that can be
        reset easily after each test.

        If any test case perform a core operation such as:
            - creating a core,
            - renaming a core,
            - unloading a core,
            - swapping a core,
        leaves state behind and the next run encounters it, Solr will raise a
        "core already exists" error or another core-related error depending on the
        operation.

        Notes:
            - Unloading a core does not remove its `instanceDir` directory.
            - Tests can reuse that same `instanceDir` to create the core again.
        """
        demo_cores = (
            "demo_core1",
            "demo_core2",
        )

        for core in demo_cores:
            with contextlib.suppress(SolrError):
                # Ignore Solr errors during cleanup (e.g., API failures)
                self.solr_admin.unload(core)

    def test_status(self):
        """Test the status endpoint returns details for all cores and specific cores."""

        # Status of all cores
        result = self.solr_admin.status()

        assert "core0" in result["status"]

        # Status of a specific core
        result = self.solr_admin.status(core="core0")

        assert result["status"]["core0"]["name"] == "core0"

    def test_create(self):
        """Test creating a core returns a successful response."""
        result = self.solr_admin.create("demo_core1")

        assert result["responseHeader"]["status"] == 0
        assert result["core"] == "demo_core1"

    def test_reload(self):
        """Test reloading a core returns a successful response."""
        result = self.solr_admin.reload("core0")

        assert result["responseHeader"]["status"] == 0

    def test_rename(self):
        """Test renaming a core succeeds and the new name appears in the status."""

        # Create the core that will be renamed
        self.solr_admin.create("demo_core1")

        # Rename the core to a new name
        result = self.solr_admin.rename("demo_core1", "demo_core2")

        assert result["responseHeader"]["status"] == 0

        # Verify that the renamed core appears in the status response
        result_2 = self.solr_admin.status(core="demo_core2")

        assert result_2["status"]["demo_core2"]["name"] == "demo_core2"

    def test_swap(self):
        """
        Test that swapping two cores succeeds.
        ┌───────────────────────────────┬───────────────────────────────┐
        │            Before             │              After            │
        ├───────────────────────────────┼───────────────────────────────┤
        │ demo_core1/core.properties    │ demo_core1/core.properties    │
        │     → name = demo_core1       │     → name = demo_core2       │
        ├───────────────────────────────┼───────────────────────────────┤
        │ demo_core2/core.properties    │ demo_core2/core.properties    │
        │     → name = demo_core2       │     → name = demo_core1       │
        └───────────────────────────────┴───────────────────────────────┘
        """
        self.solr_admin.create("demo_core1")
        self.solr_admin.create("demo_core2")

        # Perform swap
        result = self.solr_admin.swap("demo_core1", "demo_core2")

        assert result["responseHeader"]["status"] == 0

    def test_unload(self):
        """
        Test that unloading a core returns a successful JSON response.

        This test creates a core, unloads it, and verifies that the response
        contains a status of 0.
        """
        self.solr_admin.create("demo_core1")

        result = self.solr_admin.unload("demo_core1")

        assert result["responseHeader"]["status"] == 0

    def test_load(self):
        with pytest.raises(NotImplementedError):
            self.solr_admin.load("wheatley")

    def test_status__nonexistent_core_returns_empty_response(self):
        """Test that requesting status for a missing core returns an empty response."""
        result = self.solr_admin.status(core="not_exists")

        assert "name" not in result["status"]["not_exists"]
        assert "instanceDir" not in result["status"]["not_exists"]

    def test_create__existing_core_raises_error(self):
        """Test creating a core that already exists raises SolrError."""

        # First create succeeds
        self.solr_admin.create("demo_core1")

        # Second create should raise SolrError
        with pytest.raises(SolrError) as exc_info:
            self.solr_admin.create("demo_core1")

        # Check error message contents
        message = str(exc_info.value)
        assert "Solr returned HTTP error 500" in message
        assert "Core with name 'demo_core1' already exists" in message

    def test_reload__nonexistent_core_raises_error(self):
        """Test that reloading a non-existent core raises SolrError."""

        with pytest.raises(SolrError) as exc_info:
            self.solr_admin.reload("not_exists")

        message = str(exc_info.value)
        assert "Solr returned HTTP error 400" in message
        assert "No such core" in message
        assert "not_exists" in message

    def test_rename__nonexistent_core_no_effect(self):
        """
        Test that renaming a non-existent core has no effect on target core.

        Solr silently ignores rename operations when the source core does not exist.
        This test verifies that attempting to rename a missing core does not create
        the target core and does not modify any core state.
        """

        # Attempt to rename a core that does not exist (this should have no effect)
        self.solr_admin.rename("not_exists", "demo_core99")

        # Check the status of the target core to verify the rename had no effect
        result = self.solr_admin.status(core="demo_core99")

        # The target core should not exist because the rename operation was ignored
        assert "name" not in result["status"]["demo_core99"]
        assert "instanceDir" not in result["status"]["demo_core99"]

    def test_swap__missing_source_core_returns_error(self):
        """Test swapping when the source core is missing raises SolrError."""

        # Create only the target core
        self.solr_admin.create("demo_core2")

        with pytest.raises(SolrError) as ctx:
            self.solr_admin.swap("not_exists", "demo_core2")

        assert "Solr returned HTTP error 400" in str(ctx.value)
        assert "No such core" in str(ctx.value)
        assert "not_exists" in str(ctx.value)

    def test_swap__missing_target_core_returns_error(self):
        """Test swapping when the target core is missing raises SolrError."""

        # Create only the source core
        self.solr_admin.create("demo_core1")

        with pytest.raises(SolrError) as ctx:
            self.solr_admin.swap("demo_core1", "not_exists")

        assert "Solr returned HTTP error 400" in str(ctx.value)
        assert "No such core" in str(ctx.value)
        assert "not_exists" in str(ctx.value)

    def test_unload__nonexistent_core_returns_error(self):
        """Test unloading a non-existent core raises SolrError."""

        with pytest.raises(SolrError) as exc_info:
            self.solr_admin.unload("not_exists")

        message = str(exc_info.value)
        assert "Solr returned HTTP error 400" in message
        assert "Cannot unload non-existent core" in message
        assert "not_exists" in message


class TestSolrNodeAdmin:
    """Test the SolrNodeAdmin class."""

    @classmethod
    def setup_class(cls):
        """
        Initialize a shared SolrNodeAdmin instance for all test methods.
        """
        cls.solr_node = SolrNodeAdmin("http://localhost:8983/solr")

    def test_system(self):
        """Test system endpoint returns expected structure."""
        result = self.solr_node.system()

        assert result["responseHeader"]["status"] == 0
        assert "jvm" in result
        assert "system" in result

    def test_threads(self):
        """Test threads endpoint returns data."""
        result = self.solr_node.threads()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_logging(self):
        """Test logging endpoint returns configuration."""
        result = self.solr_node.logging()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_properties(self):
        """
        Test that the properties endpoint returns a non-empty response.

        Verify that the response contains system properties.
        """
        result = self.solr_node.properties()

        assert isinstance(result, dict)
        assert len(result) > 0
        assert "system.properties" in result

    def test_version(self):
        """Test version returns valid string."""
        version = self.solr_node.version()

        assert isinstance(version, str)
        assert "." in version  # e.g. "9.10.1"

    def test_version_tuple(self):
        """Test version_tuple returns normalized tuple."""
        version_tuple = self.solr_node.version_tuple()

        assert isinstance(version_tuple, tuple)
        assert len(version_tuple) == 3
        assert all(isinstance(v, int) for v in version_tuple)

    def test_memory_usage_ratio(self):
        """Test memory usage ratio is between 0 and 1."""
        ratio = self.solr_node.memory_usage_ratio()

        assert isinstance(ratio, float)
        assert 0 <= ratio <= 1

    def test_uptime_seconds(self):
        """Test uptime returns increasing float value."""
        uptime1 = self.solr_node.uptime_seconds()
        uptime2 = self.solr_node.uptime_seconds()

        assert isinstance(uptime1, float)
        assert uptime2 >= uptime1

    def test_is_healthy(self):
        """Test Solr health status."""
        assert self.solr_node.is_healthy() is True

    def test_cpu_load(self):
        """Test cpu load returns float."""
        load = self.solr_node.cpu_load()

        assert isinstance(load, float)

    def test_memory_used_mb(self):
        """Test memory usage in MB."""
        mem = self.solr_node.memory_used_mb()

        assert isinstance(mem, float)
        assert mem > 0

    def test_java_version(self):
        """Test Java version is returned."""
        version = self.solr_node.java_version()

        assert isinstance(version, str)

    def test_solr_home(self):
        """Test Solr home path is returned."""
        path = self.solr_node.solr_home()

        assert isinstance(path, str)
        assert path != ""

    def test_solr_install_dir(self):
        """Test Solr installation directory is returned."""
        path = self.solr_node.solr_install_dir()

        assert isinstance(path, str)
        assert path != ""

    def test_mode(self):
        """Test mode returns valid Solr running mode."""
        mode = self.solr_node.mode()

        assert isinstance(mode, str)
        assert mode in ("std", "solrcloud")

    def test_is_standalone(self):
        """Test standalone mode detection."""
        mode = self.solr_node.mode()

        if mode == "std":
            assert self.solr_node.is_standalone() is True
            assert self.solr_node.is_solrcloud() is False
        else:
            assert self.solr_node.is_standalone() is False

    def test_is_solrcloud(self):
        """Test SolrCloud mode detection."""
        mode = self.solr_node.mode()

        if mode == "solrcloud":
            assert self.solr_node.is_solrcloud() is True
            assert self.solr_node.is_standalone() is False
        else:
            assert self.solr_node.is_solrcloud() is False

    def test_port(self):
        """Test port is integer."""
        port = self.solr_node.port()

        assert isinstance(port, int)
        assert port > 0

    def test_os_info(self):
        """Test OS info structure."""
        os_info = self.solr_node.os_info()

        assert "name" in os_info
        assert "version" in os_info
        assert "arch" in os_info

    def test_summary(self):
        """Test summary contains key metrics."""
        summary = self.solr_node.summary()

        assert "version" in summary
        assert "mode" in summary
        assert "uptime_sec" in summary
        assert "memory_usage" in summary
        assert "cpu_load" in summary
        assert "healthy" in summary
