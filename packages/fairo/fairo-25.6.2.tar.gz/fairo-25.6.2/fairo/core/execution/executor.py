import json
import os
import types
from typing import List, Any, Callable, Dict, Union
from langchain_core.runnables import RunnableLambda, RunnableSequence
import logging

import mlflow

from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec
from fairo.core.agent.base_agent import SimpleAgent
from fairo.core.client.client import BaseClient
from fairo.core.execution.env_finder import read_variables
from fairo.core.runnable.runnable import Runnable
from fairo.core.workflow.utils import output_workflow_process_graph
from fairo.settings import get_fairo_api_key, get_fairo_api_secret, get_mlflow_experiment_name, get_mlflow_server, get_fairo_base_url

# Optional interfaces/types
class LLMAgentOutput:
    pass

logger = logging.getLogger(__name__)

class FairoExecutor:
    def __init__(
        self,
        agents: List[Any],
        verbose: bool = False,
        patch_run_output_json: Callable[[LLMAgentOutput], None] = None,
        workflow_run_id: str = "",
        runnable: Runnable = None,
        experiment_name: str = None
    ):
        self.agents = agents
        self.verbose = verbose
        self.patch_run_output_json = patch_run_output_json
        self.workflow_run_id = workflow_run_id
        self.runnable = runnable
        self.experiment_name = experiment_name if experiment_name else get_mlflow_experiment_name()
        self.setup_mlflow()
        self.client = BaseClient(
            base_url=get_fairo_base_url(),
            password=get_fairo_api_secret(),
            username=get_fairo_api_key()
        )
        # Inject shared attributes into agents
        for agent in self.agents:
            if hasattr(agent, 'set_client'):
                agent.set_client(self.client)
            if hasattr(agent, 'verbose'):
                agent.verbose = self.verbose

        self.pipeline = self._build_pipeline()

    def _wrap_agent_runnable(self, agent, input_key: str, output_key: str) -> RunnableLambda:
        """
        Wraps the agent's .run() method into a RunnableLambda with a custom function name.
        Properly propagates errors instead of continuing to the next agent.
        """
        def base_fn(inputs: Dict[str, Any]) -> Dict[str, Any]:
            if self.verbose:
                logger.info(f"[{agent.__class__.__name__}] received input: {inputs}")
            
            # Run the agent, but don't catch exceptions - let them propagate
            # This will stop the entire pipeline on agent failure
            result = agent.run(inputs[input_key])
            
            # Check if result starts with "An error occurred" which indicates agent failure
            if isinstance(result, str) and result.startswith("An error occurred during execution:"):
                # Propagate the error by raising an exception to stop the execution
                raise RuntimeError(f"Agent {agent.__class__.__name__} failed: {result}")
                
            return {output_key: result}

        # Clone function and set custom name
        fn_name = f"runnable_{agent.__class__.__name__.lower().replace(' ', '_')}"
        runnable_fn = types.FunctionType(
            base_fn.__code__,
            base_fn.__globals__,
            name=fn_name,
            argdefs=base_fn.__defaults__,
            closure=base_fn.__closure__,
        )

        return RunnableLambda(runnable_fn)

    def _build_pipeline(self) -> RunnableSequence:
        if not self.agents:
            raise ValueError("At least one agent must be provided.")

        # Assign input/output keys
        for i, agent in enumerate(self.agents):
            agent.input_key = "input" if i == 0 else f"output_{i - 1}"
            agent.output_key = f"output_{i}"

        runnables = []
        for agent in self.agents:
            runnables.append(
                self._wrap_agent_runnable(agent, agent.input_key, agent.output_key)
            )
        first_input_key = self.agents[0].input_key
        last_output_key = self.agents[-1].output_key
        # Build RunnableSequence from all steps
        pipeline = runnables[0]
        for r in runnables[1:]:
            pipeline = pipeline | r  # chaining
        
        def save_process_graph():
            process_graph = (
                output_workflow_process_graph(self.agents)
                if all(isinstance(agent, SimpleAgent) for agent in self.agents)
                else None
            )
            if len(self.agents) > 1:
                type = "Workflow"
            else:
                type = "Agent"
            fairo_settings = {
                "type": type,
                "process_graph": process_graph,
            }
            if process_graph:
                mlflow.log_text(json.dumps(fairo_settings, ensure_ascii=False, indent=2), artifact_file="fairo_settings.txt")
        save_process_graph()
        try:
            # Find environment variables used in the project
            all_env_vars = read_variables()
            # Log the file as an artifact
            mlflow.log_text(all_env_vars, artifact_file="environment/variables.txt")
            if self.verbose:
                logger.info(f"Logged {len(all_env_vars)} environment variables as artifact")
        except Exception as e:
            logger.warning(f"Failed to log environment variables: {str(e)}")

        input_schema = Schema([
            ColSpec(type="string", name=first_input_key),
        ])

        output_schema = Schema([
            ColSpec(type="string", name=last_output_key),
        ])
        model_info = mlflow.langchain.log_model(
            pipeline,
            artifact_path="",
            signature=ModelSignature(inputs=input_schema, outputs=output_schema)
        )
        # If runnable object was added, check if it exists, if yes, just set tags for the trace, otherwise create it
        if self.runnable:
            if not self.runnable.id:
                result = mlflow.register_model(
                    model_uri=model_info.model_uri,
                    name=self.runnable.name,
                    await_registration_for=0
                )
                self.runnable.create_version(
                    artifact_path=result.source,
                    registered_model_id=f"models:/{self.runnable.name}/{result.version}"
                )
            mlflow.set_tags({
                "runnable_id": self.runnable.id,
                "environment": "development",
            })
        else:
            mlflow.set_tags({
                "environment": "development",
            })   
        return pipeline

    def run(self, input_data: Union[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Execute the pipeline using the provided input.
        Properly handles and propagates errors from agents.
        """
        first_input_key = getattr(self.agents[0], 'input_key', 'input')

        # Normalize input
        if isinstance(input_data, str):
            input_data = {first_input_key: input_data}
        elif first_input_key not in input_data:
            raise ValueError(f"Missing required input key: '{first_input_key}'")

        if self.verbose:
            logger.info("Running agent pipeline...")
            logger.info(f"Initial input: {input_data}")

        try:
            # Run the pipeline but don't catch exceptions
            result = self.pipeline.invoke(input_data)
            
            if self.verbose:
                logger.info("Pipeline execution completed")
                logger.info(f"Final output: {result}")
                
            return result
            
        except Exception as e:
            # Log the error
            if self.verbose:
                logger.error(f"Pipeline execution failed: {str(e)}")
            
            # Propagate the exception so calling code can handle it
            raise e
    
    def setup_mlflow(self):
        def _clean_mlflow_env_vars():
            for env_var in ["MLFLOW_TRACKING_USERNAME", "MLFLOW_TRACKING_PASSWORD", "MLFLOW_TRACKING_TOKEN"]:
                if env_var in os.environ:
                    del os.environ[env_var]
        def setup_mlflow_tracking_server():
            os.environ["MLFLOW_TRACKING_USERNAME"] = get_fairo_api_key()
            os.environ["MLFLOW_TRACKING_PASSWORD"] = get_fairo_api_secret()
            mlflow.set_tracking_uri(get_mlflow_server())
            mlflow.set_experiment(experiment_name=self.experiment_name)
        _clean_mlflow_env_vars()
        setup_mlflow_tracking_server()
        with mlflow.start_run():
            mlflow.langchain.autolog(
                log_traces=True,
                log_input_examples=True,
            )
        