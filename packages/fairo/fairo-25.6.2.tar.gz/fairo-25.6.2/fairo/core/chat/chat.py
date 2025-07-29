
from langchain_community.chat_models.mlflow import ChatMlflow
from mlflow.deployments import get_deploy_client
import os

class FairoChat(ChatMlflow):
    def __init__(self, endpoint, workflow_run_id, **kwargs):
        super().__init__(
            target_uri=os.environ.get('MLFLOW_GATEWAY_URI', None),
            endpoint=endpoint,
            extra_params={"workflow_run_id": workflow_run_id},
            **kwargs
        )

    @property
    def _target_uri(self):
        return os.environ.get("MLFLOW_GATEWAY_URI", None)
    
    def invoke(self, *args, **kwargs):
        # Override invoke to use dynamic target_uri
        self.target_uri = self._target_uri
        self._client = get_deploy_client(self.target_uri)
        return super().invoke(*args, **kwargs)