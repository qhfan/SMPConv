import torch
import wandb


import models
import ckconv

# typing
from omegaconf import OmegaConf


SEQ_DATASETS = [
    "SpeechCommands",
    "CharTrajectories",
    "sMNIST",
    "sCIFAR10",
]

IMG_DATASETS = [
    "MNIST",
    "CIFAR10",
    "CIFAR100",
]


def construct_model(
    cfg: OmegaConf,
):
    """
    :param device: instance of torch.device
    :return: An instance of torch.nn.Module
    """

    # Define in_channels
    if cfg.dataset in [
        "sMNIST",
        "MNIST",
    ]:
        in_channels = 1
    elif cfg.dataset in [
        "CharTrajectories",
        "sCIFAR10",
        "CIFAR10",
        "CIFAR100",
    ]:
        in_channels = 3
        if cfg.dataset == "sCIFAR10" and cfg.dataset_params.noise_padded:
            in_channels = 96
    elif cfg.dataset in ["SpeechCommands"]:
        if cfg.dataset_params.mfcc:
            in_channels = 20
        else:
            in_channels = 1
    else:
        raise NotImplementedError(f"Not in_channels for dataset {cfg.dataset} found.")

    # Consider the exist_mask channel for irregularly sampled cases.
    if cfg.dataset_params.drop_rate != 0 and cfg.dataset in [
        "CharTrajectories",
        "SpeechCommands",
    ]:
        in_channels = in_channels + 1

    # Define output_channels
    if cfg.dataset in [
        "SpeechCommands",
        # "CharTrajectories",
        "sMNIST",
        "sCIFAR10",
        "MNIST",
        "CIFAR10",
    ]:
        out_channels = 10
    elif cfg.dataset in ["CIFAR100"]:
        out_channels = 100
    elif cfg.dataset in ["CharTrajectories"]:
        out_channels = 20
    else:
        raise NotImplementedError(f"Not in_channels for dataset {cfg.dataset} found.")

    # Define model type names
    if cfg.dataset in [
        "SpeechCommands",
        "CharTrajectories",
        "sMNIST",
        "sCIFAR10",
    ]:
        model_type = "SeqData"
    elif cfg.dataset in [
        "MNIST",
        "CIFAR10",
        "CIFAR100",
    ]:
        model_type = "Img"
    else:
        raise NotImplementedError(f"Not in_channels for dataset {cfg.dataset} found.")
    model_name = "%s_%s" % (model_type, cfg.net.type)

    # Define dim_linear: dimensionality of the data, i.e., 1 for temporal data,
    # 2 for images
    if cfg.dataset in SEQ_DATASETS:
        dim_linear = 1
    elif cfg.dataset in IMG_DATASETS:
        dim_linear = 2
    else:
        raise NotImplementedError(f"Not dim_linear for dataset {cfg.dataset} found.")

    # Append dim_linear to the kernel_config
    cfg.kernel.dim_linear = dim_linear

    # Print the defined parameters.
    print(
        f"Automatic Parameters:\n dataset = {cfg.dataset}, model_name = {model_name}, in_channels = {in_channels}, out_chanels = {out_channels}, dim_linear = {dim_linear}"
    )

    model_name = getattr(models, model_name)
    model = model_name(
        in_channels=in_channels,
        out_channels=out_channels,
        net_config=cfg.net,
        kernel_config=cfg.kernel,
        conv_config=cfg.conv,
    )

    # print number parameters
    no_params = ckconv.utils.num_params(model)
    print("Number of parameters:", no_params)
    wandb.run.summary["no_params"] = no_params
    model = torch.nn.DataParallel(model)  # Required for multi-GPU

    return model
