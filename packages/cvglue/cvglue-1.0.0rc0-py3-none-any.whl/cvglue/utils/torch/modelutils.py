import sys
from collections import OrderedDict
import torch

__all__ = ["load_network"]


def load_network(network, pretrained='', verbose=True, rank=0, local_rank=0, load_cuda=False):
    if isinstance(pretrained, str):
        if load_cuda:
            map_func = lambda storage, loc: storage.cuda(local_rank)
        else:
            map_func = lambda storage, loc: storage
        pretrained_dict = torch.load(pretrained, map_location=map_func)
    elif isinstance(pretrained, OrderedDict):
        pretrained_dict = pretrained
    else:
        raise ValueError(f'Pretrained expected str or OrderedDict, but got {type(pretrained)}.')

    if isinstance(pretrained_dict, torch.nn.Module):
        if verbose and rank == 0:
            print('Loaded nn.Module instead of StateDict.')
        return
    elif isinstance(pretrained_dict, OrderedDict):
        pretrained_dict = pretrained_dict
    else:
        raise ValueError(f'pretrained should be either StateDict or nn.Module file, but got {type(pretrained_dict)}.')

    if sys.version_info >= (3,0):
        not_initialized = set()
        not_used = set()
    else:
        from sets import Set
        not_initialized = Set()
        not_used = Set()

    try:
        network.load_state_dict(pretrained_dict)
        if verbose and rank == 0:
            print('Load model success from %s' % pretrained)
    except RuntimeError:
        model_dict = network.state_dict()
        try:
            for k, v in pretrained_dict.items():
                if k not in model_dict:
                    not_used.add(k)
            pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}
            network.load_state_dict(pretrained_dict)
            if verbose and rank == 0:
                print('Pretrained network has excessive layers; Only loading layers that are used')
        except RuntimeError:
            if verbose and rank == 0:
                print('Pretrained network has fewer layers; The following are not initialized:')
            for k, v in pretrained_dict.items():
                if v.size() == model_dict[k].size():
                    model_dict[k] = v

            for k, v in model_dict.items():
                if k not in pretrained_dict or v.size() != pretrained_dict[k].size():
                    not_initialized.add(k)

            network.load_state_dict(model_dict)
        if verbose and rank == 0:
            print(sorted(not_initialized))
    return not_initialized