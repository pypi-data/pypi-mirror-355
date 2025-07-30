import pytest

from energinetml.core.backend import AbstractBackend


@pytest.fixture
def backend():
    yield AbstractBackend()


class TestAbstractBackend:
    def test__get_available_subscriptions(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.get_available_subscriptions()

    def test__get_available_resource_groups(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.get_available_resource_groups("subscription_id")

    def test__get_available_workspaces(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.get_available_workspaces("subscription_id", "resource_group")

    def test__get_available_workspace_names(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.get_available_workspace_names("subscription_id", "resource_group")

    def test__get_workspace(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            project_meta = {
                "subscription_id": "subscription_id",
                "resource_group": "resource_group",
                "workspace_name": "name",
            }

            backend.get_workspace(project_meta)

    def test__get_local_training_context(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.get_local_training_context("force_download")

    def test__get_cloud_training_context(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.get_cloud_training_context()

    def test__submit_model(self, backend):
        """
        :param AbstractBackend backend:
        """
        with pytest.raises(NotImplementedError):
            backend.submit_model("model", "params")
