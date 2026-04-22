import contextlib
from unittest.mock import Mock

import pytest
import requests

from pysolr import SolrCoreAdmin, SolrError, SolrNodeAdmin


class TestSolrCoreAdmin:
    """Test the SolrCoreAdmin class."""

    @classmethod
    def setup_class(cls):
        """
        Initialize a shared SolrCoreAdmin instance for all test methods.
        """
        cls.solr_admin = SolrCoreAdmin("http://localhost:8983/solr/admin/cores")

    @classmethod
    def teardown_class(cls):
        """Close the shared requests session (if created) after all tests."""
        session = getattr(cls.solr_admin, "session", None)
        if session is not None:
            session.close()

    def setup_method(self):
        """
        Ensure no demo cores or related state remain before each test.
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

    @classmethod
    def teardown_class(cls):
        """Close the shared requests session (if created) after all tests."""
        session = getattr(cls.solr_node, "session", None)
        if session is not None:
            session.close()

    def _stubbed_node(self, response=None):
        """
        Return a node admin of its own, for tests that stub its responses.

        Stubbing the shared instance would leak into the tests that run after.

        :param response: response its session answers every request with
        """
        node = SolrNodeAdmin(self.solr_node.url)

        if response is not None:
            node.session = Mock(**{"get.return_value": response})

        return node

    @staticmethod
    def _http_error_response(status_code):
        """
        Return a response that fails with ``status_code``, as requests does.

        :param status_code: HTTP status Solr answered with
        """
        response = Mock(status_code=status_code, headers={}, text="")
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )

        return response

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
        assert "loggers" in result

    def test_logging__since_returns_buffered_events(self):
        """Test that `since` switches the response to the log event history."""
        result = self.solr_node.logging(since=0)

        assert "info" in result
        assert "history" in result

    def test_set_log_level(self):
        """Test that a logger level can be set and unset at runtime."""
        logger = "org.apache.solr"

        try:
            result = self.solr_node.set_log_level(logger, "DEBUG")

            assert result["responseHeader"]["status"] == 0

            levels = {
                entry["name"]: entry for entry in self.solr_node.logging()["loggers"]
            }
            assert levels[logger]["level"] == "DEBUG"
        finally:
            self.solr_node.set_log_level(logger, "unset")

    def test_health(self):
        """Test the health endpoint reports the node as healthy."""
        result = self.solr_node.health()

        assert result["responseHeader"]["status"] == 0
        assert result["status"] == "OK"

    def test_health__require_healthy_cores(self):
        """Test that the health check also accepts the stricter core check."""
        result = self.solr_node.health(require_healthy_cores=True)

        assert result["status"] == "OK"

    def test_health__max_generation_lag(self):
        """
        Test the replication lag check of user-managed clusters.

        Passing the limit is what enables the check, so Solr stops reporting
        that it is skipping it.
        """
        result = self.solr_node.health(max_generation_lag=10)

        assert result["status"] == "OK"
        assert "maxGenerationLag isn't specified" not in result.get("message", "")

    def test_key(self):
        """Test that the node returns its PKI public key."""
        key = self.solr_node.key()

        assert isinstance(key, str)
        assert key != ""

    def test_metrics(self):
        """
        Test that metrics are returned in whichever format the node serves.

        Solr 9 answers with JSON, Solr 10 with Prometheus exposition text.
        """
        result = self.solr_node.metrics()

        if self.solr_node.version_tuple()[0] >= 10:
            assert isinstance(result, str)
            assert "jvm_" in result
        else:
            assert isinstance(result, dict)
            assert "metrics" in result

    def test_zookeeper_status(self):
        """Test ZooKeeper status, which a standalone node refuses to report."""
        if self.solr_node.is_solrcloud():
            assert self.solr_node.zookeeper_status()["responseHeader"]["status"] == 0
        else:
            with pytest.raises(SolrError):
                self.solr_node.zookeeper_status()

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

    def test_is_healthy__unreachable_node(self):
        """Test that a node that cannot be reached is reported as unhealthy."""
        node = SolrNodeAdmin("http://localhost:18983/solr", timeout=5)

        with contextlib.closing(node.get_session()):
            assert node.is_healthy() is False

    def test_is_healthy__rejected_request_raises_error(self):
        """
        Test that a URL Solr rejects raises instead of reporting a down node.

        Answering False there would report a client mistake as an unhealthy
        node.
        """
        node = SolrNodeAdmin(f"{self.solr_node.url}/not-a-node", timeout=5)

        with contextlib.closing(node.get_session()), pytest.raises(SolrError):
            node.is_healthy()

    @pytest.mark.parametrize("status_code", [500, 502, 503])
    def test_is_healthy__server_error_is_not_an_error(self, status_code):
        """
        Test that a node answering 5xx is unhealthy rather than raising.

        Solr answers 503 whenever the health check itself fails, such as a node
        that lost ZooKeeper or has cores still recovering.
        """
        node = self._stubbed_node(self._http_error_response(status_code))

        assert node.is_healthy() is False

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404])
    def test_is_healthy__rejected_status_raises_error(self, status_code):
        """Test that every 4xx raises, since Solr rejected the request."""
        node = self._stubbed_node(self._http_error_response(status_code))

        with pytest.raises(SolrError):
            node.is_healthy()

    def test_is_healthy__connection_error_is_not_an_error(self):
        """Test that a node refusing the connection is unhealthy."""
        node = self._stubbed_node()
        node.session = Mock(
            **{"get.side_effect": requests.exceptions.ConnectionError("refused")}
        )

        assert node.is_healthy() is False

    def test_is_healthy__error_without_a_response_is_not_an_error(self):
        """Test that a SolrError carrying no HTTP response reports unhealthy."""
        node = self._stubbed_node()
        node.health = Mock(side_effect=SolrError("no response to read a status from"))

        assert node.is_healthy() is False

    def test_cpu_usage_ratio(self):
        """Test cpu usage is a ratio, or -1 where the JVM cannot report it."""
        usage = self.solr_node.cpu_usage_ratio()

        assert isinstance(usage, float)
        assert usage == -1 or 0 <= usage <= 1

    def test_load_average(self):
        """Test load average returns float."""
        load = self.solr_node.load_average()

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

    def test_timezone(self):
        """Test JVM timezone is returned."""
        timezone = self.solr_node.timezone()

        assert isinstance(timezone, str)
        assert timezone != ""

    @pytest.mark.parametrize("port_property", ["jetty.port", "solr.port.listen"])
    def test_port__solr_9_and_10_property_names(self, port_property):
        """Test that the port is read from the property name of either version."""
        node = self._stubbed_node()
        node.properties = Mock(
            return_value={"system.properties": {port_property: "8983"}}
        )

        assert node.port() == 8983

    def test_port__missing_property_raises_error(self):
        """Test that a response without a port property raises SolrError."""
        node = self._stubbed_node()
        node.properties = Mock(return_value={"system.properties": {}})

        with pytest.raises(SolrError, match="Unable to determine the Solr port"):
            node.port()

    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("9.10.1", (9, 10, 1)),
            ("10.0.0", (10, 0, 0)),
            ("10.0.0-SNAPSHOT", (10, 0, 0)),
            ("9.10", (9, 10, 0)),
        ],
    )
    def test_version_tuple__normalizes_versions(self, version, expected):
        """Test that qualifiers are dropped and short versions are padded."""
        node = self._stubbed_node()
        node.system = Mock(return_value={"lucene": {"solr-spec-version": version}})

        assert node.version_tuple() == expected

    def test_version_tuple__unparsable_version_raises_error(self):
        """Test that a non-numeric version raises SolrError."""
        node = self._stubbed_node()
        node.system = Mock(return_value={"lucene": {"solr-spec-version": "nine.ten"}})

        with pytest.raises(SolrError, match="Invalid Solr version format"):
            node.version_tuple()

    def test_missing_key_raises_error(self):
        """Test that a response without the expected keys raises SolrError."""
        node = self._stubbed_node()
        node.system = Mock(return_value={"jvm": {}})

        with pytest.raises(SolrError, match="Unable to determine the uptime"):
            node.uptime_seconds()

    def test_unexpected_response_shape_raises_error(self):
        """Test that a response nested differently than expected raises SolrError."""
        node = self._stubbed_node()
        node.system = Mock(return_value={"system": "unavailable"})

        with pytest.raises(SolrError, match="Unable to determine the CPU load"):
            node.cpu_usage_ratio()

    def test_is_healthy__unhealthy_node(self):
        """Test that a node reporting a failure is not healthy."""
        node = self._stubbed_node()
        node.health = Mock(return_value={"status": "FAILURE"})

        assert node.is_healthy() is False

    def test_metrics__json_response_is_decoded(self):
        """Test that the JSON metrics of Solr 9 are returned decoded."""
        payload = {"metrics": {"solr.jvm": {"memory.heap.used": 1}}}
        node = self._stubbed_node(
            Mock(
                headers={"Content-Type": "application/json;charset=utf-8"},
                **{"json.return_value": payload},
            )
        )

        assert node.metrics(group="jvm") == payload

    def test_metrics__prometheus_response_is_returned_as_text(self):
        """Test that the Prometheus metrics of Solr 10 are returned unparsed."""
        exposition = "# TYPE jvm_memory_used gauge\njvm_memory_used 1\n"
        node = self._stubbed_node(
            Mock(
                headers={"Content-Type": "text/plain; version=0.0.4"},
                text=exposition,
            )
        )

        assert node.metrics() == exposition
