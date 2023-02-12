from dataclasses import dataclass

import torch
from diffusers import (
    DiffusionPipeline,
    StableDiffusionDepth2ImgPipeline,
    StableDiffusionPipeline,
    StableDiffusionUpscalePipeline,
)


@dataclass
class StableDiffusionV1:
    repo_name = "runwayml/stable-diffusion-v1-5"
    pipeline = StableDiffusionPipeline


@dataclass
class StableDiffusionV2Base:
    repo_name = "stabilityai/stable-diffusion-2-base"
    scheduler = True
    num_inference_steps = 25
    pipeline = StableDiffusionPipeline


@dataclass
class StableDiffusionV2:
    repo_name = "stabilityai/stable-diffusion-2"
    scheduler = True
    num_inference_steps = 25
    guidance_scale = 9
    pipeline = DiffusionPipeline


@dataclass
class StableDiffusion4xUpscale:
    repo_name = "stabilityai/stable-diffusion-x4-upscaler"
    pipeline = StableDiffusionUpscalePipeline
    torch_dtype = torch.float16


@dataclass
class StableDiffusionDepth2Img:
    repo_name = "stabilityai/stable-diffusion-2-depth"
    pipeline = StableDiffusionDepth2ImgPipeline
    strength = 0.7


DEFAULT_MODELS = (
    StableDiffusionV1,
    StableDiffusionV2,
    StableDiffusionV2Base,
    StableDiffusion4xUpscale,
    StableDiffusionDepth2Img,
)