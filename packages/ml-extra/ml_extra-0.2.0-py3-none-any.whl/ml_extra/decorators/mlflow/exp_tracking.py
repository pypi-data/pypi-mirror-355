
from ml_extra.experiment_tracking.mlflow.experiments import get_or_create_experiment
import mlflow
from pathlib import Path
import os 
from typing import Optional
from typing import Dict


def mlflow_experiment(name: str, tags: Optional[Dict[str, str]] = None, return_experiment: bool = False):
    """
    Decorator to set the MLflow experiment name and tags.
    This decorator creates a new experiment if it doesn't exist.
    The decorator modifies the function to accept an `experiment` argument,
    which is the MLflow experiment object.

    :param name: The name of the MLflow experiment.
    :param tags: A dictionary of tags to associate with the experiment.
    :param return_experiment: If True, the decorated function will return the experiment object.
    :return: A decorator function that sets the MLflow experiment.
    """

    def decorator(func, name=name, tags=tags, return_experiment=return_experiment):
        """
        Decorator function to set the MLflow experiment name and tags.
        It creates a new experiment if it doesn't exist.
        The decorator modifies the function to accept an `experiment` argument,
        which is the MLflow experiment object.

        :param func: The function to be decorated.
        :param name: The name of the MLflow experiment.
        :param tags: A dictionary of tags to associate with the experiment.
        :return: The decorated function with the MLflow experiment set.
        """

        def wrapper(*args, **kwargs):
            print(f"Setting MLflow experiment: {name}")
            experiment = get_or_create_experiment(name=name, tags=tags)
            if return_experiment:
                kwargs["mlflow_experiment"] = experiment            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def mlflow_client(func):
    """
    Decorator to pass the MLflow client as argument to the function.
    """
    def wrapper(*args, **kwargs):
        print("Setting MLflow client...")
        mlflow_client = mlflow.MlflowClient()
        kwargs["mlflow_client"] = mlflow_client
        return func(*args, **kwargs)

    return wrapper


def mlflow_tracking_uri(func):
    """
    Set the MLflow tracking URI to the local file system.
    """
    def wrapper(*args, **kwargs):
        print("Setting MLflow tracking URI...")
        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", None)
        if mlflow_tracking_uri is None:
            print("MLFLOW_TRACKING_URI not set. Using default local file system.")
            current_directory = Path.cwd() / "mlruns"
            mlflow.set_tracking_uri(current_directory.as_uri())
        elif not mlflow.get_tracking_uri() and mlflow_tracking_uri:
            print(f"Using MLFLOW_TRACKING_URI: {mlflow_tracking_uri}")
            tracking_uri_path = Path(mlflow_tracking_uri)
            mlflow.set_tracking_uri(tracking_uri_path.as_uri())
        
        return func(*args, **kwargs)

    return wrapper
