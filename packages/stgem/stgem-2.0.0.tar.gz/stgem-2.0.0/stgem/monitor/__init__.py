from stgem.features import FeatureVector

class Monitor(object):
    """
    Base class for monitor objects.
    """
    def __call__(self, obj: FeatureVector | dict, strict_horizon_check=True, scale=False) -> float:
        """
        Evaluate the monitor with the given feature vector or dictionary.

        Args:
            obj (FeatureVector | dict): The input feature vector or dictionary.
            strict_horizon_check (bool, optional): Whether to strictly check the horizon. Default is True.
            scale (bool, optional): Whether to scale the robustness value. Default is False.

        Returns:
            float: The evaluated robustness value.

        Raises:
            NotImplementedError: If the method is not implemented by subclasses.
        """        
        raise NotImplementedError


