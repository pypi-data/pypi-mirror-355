from typing import List, Dict

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


def add_params(before: dict, after: dict) -> dict:
    """
    Add two PyTorch state_dicts: delta = before + after
    """
    return {
        key: before[key] + after[key]
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


def average_states(states: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    avg_state = {}
    for key in states[0]:
        stacked = torch.stack([state[key] for state in states], dim=0)
        avg_state[key] = stacked.mean(dim=0)
    return avg_state
