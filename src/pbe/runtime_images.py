"""Resolve pinned OCI identities without relying on Docker's image store format."""
from functools import lru_cache
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import uuid
from .io import read, write


def _hex(image):
    if not isinstance(image, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("Runtime images must use full SHA-256 digests.")
    return image.split(":")[1]


def _digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_proof(image, chain):
    _hex(image)
    if not isinstance(chain, list) or not chain or not all(isinstance(x, str) for x in chain):
        raise ValueError("Invalid runtime image proof.")
    if _digest(chain[0]) != image:
        raise ValueError("Runtime proof does not match the pinned image.")
    documents = [json.loads(text) for text in chain]
    if not all(isinstance(doc, dict) for doc in documents):
        raise ValueError("Invalid runtime image metadata.")
    config = documents[-1]
    if not config.get("os") or not config.get("architecture") or not isinstance(config.get("rootfs", {}).get("diff_ids"), list):
        raise ValueError("Runtime proof must end in an image configuration.")
    for position, document in enumerate(documents[:-1]):
        if "manifests" in document:
            descriptors = document["manifests"]
        elif "config" in document and position == len(documents) - 2:
            descriptors = [document["config"]]
        else:
            raise ValueError("Broken runtime image proof chain.")
        following = chain[position + 1]
        matches = [d for d in descriptors if d.get("digest") == _digest(following)
                   and d.get("size") == len(following.encode("utf-8"))]
        if not matches:
            raise ValueError("Runtime proof descriptor mismatch.")
        platform = matches[0].get("platform", {})
        if any(platform.get(key, config.get(key)) != config.get(key) for key in ("os", "architecture")):
            raise ValueError("Runtime proof platform mismatch.")
    return _digest(chain[-1]), config


def archive_proofs(path, images):
    proofs = {}
    platform = None
    with tarfile.open(path, "r:") as archive:
        def blob(image):
            name = "blobs/sha256/" + _hex(image)
            try:
                member = archive.getmember(name)
            except KeyError:
                return None
            if not member.isfile():
                raise ValueError("Invalid runtime metadata member: " + name)
            text = archive.extractfile(member).read().decode("utf-8")
            if _digest(text) != image:
                raise ValueError("Runtime metadata checksum mismatch: " + image)
            return text

        for image in sorted(set(images)):
            text = blob(image)
            if text is None:
                continue
            chain = []
            while True:
                if text in chain:
                    raise ValueError("Cyclic runtime image metadata.")
                chain.append(text)
                document = json.loads(text)
                if "rootfs" in document:
                    break
                if "manifests" in document:
                    if platform is None:
                        result = subprocess.run(["docker", "version", "--format", "{{.Server.Os}}/{{.Server.Arch}}"],
                                                capture_output=True, text=True, check=True, timeout=30)
                        platform = result.stdout.strip()
                    candidates = [d for d in document["manifests"]
                                  if "/".join(d.get("platform", {}).get(k, "") for k in ("os", "architecture")) == platform]
                    if len(candidates) != 1:
                        raise ValueError("No unique runtime image for Docker platform " + platform)
                    descriptor = candidates[0]
                elif "config" in document:
                    descriptor = document["config"]
                else:
                    break
                text = blob(descriptor["digest"])
                if text is None:
                    raise ValueError("Missing runtime image metadata: " + descriptor["digest"])
            validate_proof(image, chain)
            proofs[image] = chain
    return proofs


def _inspect(image):
    result = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True, timeout=30)
    if result.returncode:
        return None
    values = json.loads(result.stdout)
    return values[0] if len(values) == 1 else None


def _verified_local(image, chain, aliases=()):
    local, config = validate_proof(image, chain)
    inspected = _inspect(local)
    if not inspected or inspected.get('Id') != local:
        inspected = None
        for alias in aliases:
            candidate = _digest(alias[0])
            config_digest, _ = validate_proof(candidate, alias)
            if config_digest != local:
                raise ValueError('Runtime alias changes the pinned configuration.')
            found = _inspect(candidate)
            if found and found.get('Id') == candidate:
                local, inspected = candidate, found
                break
        if inspected is None:
            raise ValueError("Runtime image configuration is not loaded: " + local)
    if (inspected.get("Os") != config["os"] or inspected.get("Architecture") != config["architecture"]
            or inspected.get("RootFS", {}).get("Layers", []) != config["rootfs"]["diff_ids"]):
        raise ValueError("Loaded runtime image does not match its proof: " + image)
    return local


def proof_path(root, image):
    return root / ".cache/runtime-images" / (_hex(image) + ".json")


def remember_proofs(root, proofs, aliases=None):
    aliases = aliases or {}
    for image, chain in proofs.items():
        validate_proof(image, chain)
        inspected = _inspect(image)
        if not inspected or inspected.get("Id") != image:
            _verified_local(image, chain, aliases.get(image, []))
    for image, chain in proofs.items():
        path = proof_path(root, image)
        temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
        write(temporary, chain)
        temporary.replace(path)
        if image in aliases:
            write(path.with_suffix('.local.json'), aliases[image])
    resolve_image.cache_clear()


@lru_cache(maxsize=128)
def resolve_image(root, image):
    _hex(image)
    inspected = _inspect(image)
    if inspected and inspected.get("Id") == image:
        return image
    path = proof_path(root, image)
    if path.is_file():
        local = path.with_suffix('.local.json')
        return _verified_local(image, read(path), read(local) if local.is_file() else [])
    raise ValueError(f"Missing runtime {image}. Start Docker or use 'pbe runtime load BUNDLE' to load its identity proof.")


@contextmanager
def import_archive(path, proofs):
    """Expose config-pinned images to both Docker archive readers, without changing blobs."""
    config_pins = {pin: chain for pin, chain in proofs.items() if len(chain) == 1}
    if not config_pins:
        yield path, {}
        return
    with tarfile.open(path, 'r:') as source:
        entries = json.load(source.extractfile('manifest.json'))
        by_config = {e['Config']: e for e in entries}
        index = json.load(source.extractfile('index.json')) if 'index.json' in source.getnames() else {
            'schemaVersion': 2, 'mediaType': 'application/vnd.oci.image.index.v1+json', 'manifests': []}
        additions, aliases = {}, {}
        for pin, chain in config_pins.items():
            config_name = 'blobs/sha256/' + _hex(pin)
            entry = by_config.get(config_name)
            if entry is None:
                raise ValueError('No archive layers for pinned configuration: ' + pin)
            config = json.loads(chain[0])
            layers = []
            for name in entry['Layers']:
                if not name.startswith('blobs/sha256/') or not source.getmember(name).isfile():
                    raise ValueError('Unsupported runtime layer: ' + name)
                digest = 'sha256:' + name.rsplit('/', 1)[-1]
                _hex(digest)
                layers.append(dict(mediaType='application/vnd.oci.image.layer.v1.tar',
                                   digest=digest, size=source.getmember(name).size))
            if [x['digest'] for x in layers] != config['rootfs']['diff_ids']:
                raise ValueError('Runtime layers differ from the pinned configuration.')
            manifest = json.dumps(dict(schemaVersion=2, mediaType='application/vnd.oci.image.manifest.v1+json',
                config=dict(mediaType='application/vnd.oci.image.config.v1+json', digest=pin,
                            size=len(chain[0].encode('utf-8'))), layers=layers), separators=(',', ':'))
            digest = _digest(manifest)
            additions['blobs/sha256/' + _hex(digest)] = manifest.encode('utf-8')
            aliases[pin] = [[manifest, chain[0]]]
            descriptor = dict(mediaType='application/vnd.oci.image.manifest.v1+json', digest=digest,
                              size=len(manifest.encode('utf-8')),
                              platform={k: config[k] for k in ('os', 'architecture')})
            if not any(x['digest'] == digest for x in index['manifests']):
                index['manifests'].append(descriptor)
        additions['index.json'] = json.dumps(index, separators=(',', ':')).encode('utf-8')
        additions['oci-layout'] = b'{"imageLayoutVersion":"1.0.0"}'
        with tempfile.TemporaryDirectory(prefix='pbe-runtime-') as temporary:
            target = Path(temporary) / 'images.tar'
            with tarfile.open(target, 'w') as output:
                for member in source:
                    if member.name not in additions:
                        output.addfile(member, source.extractfile(member) if member.isfile() else None)
                for name, content in additions.items():
                    member = tarfile.TarInfo(name)
                    member.size = len(content)
                    output.addfile(member, io.BytesIO(content))
            yield target, aliases
