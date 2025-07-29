import abc
import asyncio
import dataclasses
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

import numpy as np
import polars as pl

from corvic import eorm
from corvic.result import InternalError, InvalidArgumentError, Ok

if TYPE_CHECKING:
    from transformers.models.auto.modeling_auto import AutoModel
    from transformers.models.auto.processing_auto import AutoProcessor


@dataclasses.dataclass
class EmbedTextContext:
    """Data to be embedded and arguments to describe how to embed them."""

    inputs: Sequence[str] | pl.Series
    model_name: str
    tokenizer_name: str
    expected_vector_length: int
    expected_coordinate_bitwidth: Literal[32, 64]
    room_id: eorm.RoomID


@dataclasses.dataclass
class EmbedTextResult:
    """The result of running text embedding on an EmbedTextContext."""

    context: EmbedTextContext
    embeddings: pl.Series


class TextEmbedder(Protocol):
    """Use a model to embed text."""

    async def aembed(
        self,
        context: EmbedTextContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> Ok[EmbedTextResult] | InvalidArgumentError | InternalError: ...


@dataclasses.dataclass
class EmbedImageContext:
    """Data to be embedded and arguments to describe how to embed them."""

    inputs: Sequence[bytes] | pl.Series
    model_name: str
    expected_vector_length: int
    expected_coordinate_bitwidth: Literal[32, 64]


@dataclasses.dataclass
class EmbedImageResult:
    """The result of running Image embedding on an EmbedImageContext."""

    context: EmbedImageContext
    embeddings: pl.Series


class ImageEmbedder(Protocol):
    """Use a model to embed text."""

    @classmethod
    def model_name(cls) -> str: ...

    async def aembed(
        self,
        context: EmbedImageContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> Ok[EmbedImageResult] | InvalidArgumentError | InternalError: ...


@dataclasses.dataclass
class LoadedModels:
    model: "AutoModel"
    processor: "AutoProcessor"


class HFModelText(TextEmbedder):
    """Generic text/image embedder from hugging face models."""

    @abc.abstractmethod
    def _load_models(self) -> LoadedModels: ...

    def embed(
        self, context: EmbedTextContext
    ) -> Ok[EmbedTextResult] | InvalidArgumentError | InternalError:
        match context.expected_coordinate_bitwidth:
            case 64:
                coord_dtype = pl.Float64()
            case 32:
                coord_dtype = pl.Float32()

        models = self._load_models()
        model = models.model
        processor = models.processor
        model.eval()  # type: ignore[reportAttributeAccess]

        import torch

        with torch.no_grad():
            inputs = cast(
                dict[str, torch.Tensor],
                processor(  # type: ignore[reportAttributeAccess]
                    text=context.inputs,
                    return_tensors="pt",
                    padding=True,
                ),
            )
            text_features = model.get_text_features(input_ids=inputs["input_ids"])  # type: ignore[reportAttributeAccess]

        text_features_numpy = cast(np.ndarray[Any, Any], text_features.numpy())  #  pyright: ignore[reportUnknownMemberType]

        return Ok(
            EmbedTextResult(
                context=context,
                embeddings=pl.Series(
                    values=text_features_numpy[:, : context.expected_vector_length],
                    dtype=pl.List(
                        coord_dtype,
                    ),
                ),
            )
        )

    async def aembed(
        self,
        context: EmbedTextContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> Ok[EmbedTextResult] | InvalidArgumentError | InternalError:
        return await asyncio.get_running_loop().run_in_executor(
            worker_threads, self.embed, context
        )


class ClipText(HFModelText):
    """Clip Text embedder.

    CLIP (Contrastive Language-Image Pre-Training) is a neural network trained
    on a variety of (image, text) pairs. It can be instructed in natural language
    to predict the most relevant text snippet, given an image, without
    directly optimizing for the task, similarly to the zero-shot capabilities of
    GPT-2 and 3. We found CLIP matches the performance of the original ResNet50
    on ImageNet "zero-shot" without using any of the original 1.28M labeled examples,
    overcoming several major challenges in computer vision.
    """

    def _load_models(self):
        from transformers.models.clip import (
            CLIPModel,
            CLIPProcessor,
        )

        model = cast(
            AutoModel,
            CLIPModel.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path="openai/clip-vit-base-patch32",
                revision="5812e510083bb2d23fa43778a39ac065d205ed4d",
            ),
        )
        processor = cast(
            AutoProcessor,
            CLIPProcessor.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path="openai/clip-vit-base-patch32",
                revision="5812e510083bb2d23fa43778a39ac065d205ed4d",
                use_fast=False,
            ),
        )
        return LoadedModels(model=model, processor=processor)


class SigLIP2Text(HFModelText):
    """SigLIP2 text/image embedder."""

    def _load_models(self):
        from transformers.models.auto.modeling_auto import AutoModel
        from transformers.models.auto.processing_auto import AutoProcessor

        model = cast(
            AutoModel,
            AutoModel.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path="google/siglip2-base-patch16-512",
                revision="a89f5c5093f902bf39d3cd4d81d2c09867f0724b",
                device_map="auto",
            ),
        )
        processor = cast(
            AutoProcessor,
            AutoProcessor.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path="google/siglip2-base-patch16-512",
                revision="a89f5c5093f902bf39d3cd4d81d2c09867f0724b",
                use_fast=True,
            ),
        )
        return LoadedModels(model=model, processor=processor)
