import argparse
import os
import time
from typing import Union

import pydantic
from pydantic import BaseModel
import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
import uvicorn
from fastapi import Body, Query, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

static_path = os.path.join(os.path.dirname(__file__), "images")


def init_diffusion(model: str):
    pipe = DiffusionPipeline.from_pretrained(model,
                                             torch_dtype=torch.float16,
                                             use_safetensors=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()
    return pipe


def image_gen(prompt):
    image = sd(prompt).images[0]
    current_timestamp = time.time_ns()
    pf = f"{current_timestamp}.png"
    m3f_path = os.path.join(static_path, pf)
    image.save(m3f_path)
    image_url = f"{external_http_url}/images/{pf}"
    return image_url


class UrlResponse(BaseModel):
    image: str = pydantic.Field("", description="image url")


async def diffusion_gen(prompt: Union[str, None] = Query(alias="prompt")):
    image_url = image_gen(prompt)
    return UrlResponse(image=image_url)


def api_start(host, port, external_url, diffusion_model):
    global app
    global sd
    global external_http_url
    external_http_url = external_url
    sd = init_diffusion(diffusion_model)
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/images", StaticFiles(directory=static_path))
    app.get("/diffusion/gen", response_model=UrlResponse)(diffusion_gen)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--host", type=str, default="127.0.0.1", help="host ip")
    parser.add_argument("--port", type=int, default=8080, help="port")
    parser.add_argument("--external_access_url", type=str, default="http://127.0.0.1:8080", help="image base url")
    parser.add_argument("--diffusion_model", type=str, default="dreamlike-art/dreamlike-diffusion-1.0",
                        help="diffusion model name")
    args = parser.parse_args()

    api_start(args.host, args.port, args.external_access_url, args.diffusion_model)
