import torch


def subtract_params(before: dict, after: dict) -> dict:
    """
    Subtract two PyTorch state_dicts: delta = before - after
    """
    return {
        key: before[key] - after[key]
        for key in before
        if key in after and isinstance(before[key], torch.Tensor)
    }


def divide_by(param_dict: dict, scalar: float) -> dict:
    """
    Divide all parameters in a PyTorch state_dict by a scalar
    """
    return {
        key: value / scalar
        for key, value in param_dict.items()
        if isinstance(value, torch.Tensor)
    }


def get_param_diff(model):
    return {k: v.cpu().detach().clone() for k, v in model.state_dict().items()}
