import hashlib
import random
from typing import Any


def _generate_random_sha():
    random_sha = hashlib.sha256(f"{random.randint(0,100)}".encode("utf-8")).hexdigest()
    return f"sha256:{random_sha}"


def _create_image_layers(no_layers: int):
    layers = []
    for _ in range(no_layers):
        layers.append(
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": random.randint(100, 1000),
                "digest": _generate_random_sha(),
            }
        )
    return layers


def _create_image_digest(layers: Any):
    layer_digests = "".join([layer["digest"] for layer in layers])
    summed_digest = hashlib.sha256(f"{layer_digests}".encode("utf-8")).hexdigest()
    return f"sha256:{summed_digest}"


def create_image_manifest():
    layers = _create_image_layers(3)
    image_digest = _create_image_digest(layers)

    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": sum([layer["size"] for layer in layers]),
            "digest": image_digest,
        },
        "layers": layers,
    }
