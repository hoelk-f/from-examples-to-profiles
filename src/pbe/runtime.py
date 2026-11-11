from pathlib import Path
import json
import re
import shutil
import subprocess
import tarfile
from .io import read, write, sha
from .runtime_images import archive_proofs, import_archive, proof_path, remember_proofs, resolve_image, validate_proof


CLASSIC = {"synthphonia": "S01", "merlin": "S02", "prose": "S03", "crossbeam": "S06", "bustle": "S08"}


def required(root, systems, synthesis=False, overrides=None):
    classic = read(root / "runtimes/classical/configuration.json")["images"]
    llm = read(root / "runtimes/llm/configuration.json")["images"]
    images = {}
    for system in systems:
        if system in CLASSIC:
            images[system] = classic[CLASSIC[system]]
        elif system == "direct-python":
            images[system] = llm["direct"]
        elif system in {'direct-dsl','hysynth-string'}:
            cfg = read(root/'runtimes/hysynth/runtime.json')
            images[system] = cfg['evaluation_image']
            if synthesis:
                images['hysynth-inspection'] = cfg['inspection_image']
                if system == 'hysynth-string':
                    images['hysynth-search'] = cfg['search_image']
        else:
            raise ValueError("Unsupported runtime: " + system)
    if overrides:
        allowed = {'direct-dsl', 'hysynth-string', 'hysynth-inspection', 'hysynth-search'}
        if set(overrides) - allowed or any(not isinstance(pin, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', pin) for pin in overrides.values()):
            raise ValueError('Versioned DSL runtimes require full SHA-256 image pins.')
        images = {label: overrides.get(label, image) for label, image in images.items()}
    return images


def ensure(root, systems, synthesis=False, overrides=None):
    if shutil.which("docker") is None:
        raise ValueError("Docker is required for execution. 'pbe report' works without it.")
    resolve_image.cache_clear()
    images = {label: resolve_image(root, image) for label, image in required(root, systems, synthesis, overrides).items()}
    if "prose" in systems:
        files = read(root / "runtimes/prose-files.json")
        for name, expected in files.items():
            path = root / "runtimes/prose" / name
            if not path.is_file() or sha(path) != expected:
                raise ValueError("Missing or changed PROSE runtime. Use 'pbe runtime load BUNDLE'.")
    return images


def export_bundle(root, destination, systems=None, overrides=None):
    systems = systems or list(CLASSIC) + ["direct-python"]
    images = ensure(root, systems, synthesis=True, overrides=overrides)
    folder = Path(destination).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    image_file = folder / "images.tar"
    subprocess.run(["docker", "image", "save", "-o", str(image_file), *sorted(set(images.values()))], check=True)
    runtime_file = folder / "prose.tar.gz"
    with tarfile.open(runtime_file, "w:gz") as archive:
        for path in sorted((root / "runtimes/prose").rglob("*")):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(root / "runtimes/prose").as_posix())
    pins = required(root, systems, synthesis=True, overrides=overrides)
    proofs = archive_proofs(image_file, pins.values())
    for image in set(pins.values()):
        path = proof_path(root, image)
        if image not in proofs and path.is_file():
            proofs[image] = read(path)
        if image in proofs:
            validate_proof(image, proofs[image])
        elif image not in images.values():
            raise ValueError("Missing runtime image proof for export: " + image)
    write(folder / "bundle.json", {"schema_version": 2, "images": pins, "image_proofs": proofs,
                                  "files": {p.name: sha(p) for p in [image_file, runtime_file]}})
    print(folder)


def load_bundle(root, source):
    folder = Path(source).resolve()
    bundle = read(folder / "bundle.json")
    if bundle.get("schema_version") not in (1, 2) or set(bundle.get("files", {})) != {"images.tar", "prose.tar.gz"}:
        raise ValueError("Unsupported runtime bundle.")
    for name, expected in bundle["files"].items():
        if sha(folder / name) != expected:
            raise ValueError("Bundle checksum mismatch: " + name)
    proofs = dict(bundle.get("image_proofs", {}))
    if set(proofs) - set(bundle["images"].values()):
        raise ValueError("Unexpected runtime image proof.")
    proofs.update(archive_proofs(folder / "images.tar", set(bundle["images"].values()) - set(proofs)))
    for image, chain in proofs.items():
        validate_proof(image, chain)
    with import_archive(folder / 'images.tar', proofs) as (archive, aliases):
        subprocess.run(["docker", "image", "load", "-i", str(archive)], check=True)
        remember_proofs(root, proofs, aliases)
    target = (root / "runtimes/prose").resolve()
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(folder / "prose.tar.gz", "r:gz") as archive:
        for item in archive.getmembers():
            path = (target / item.name).resolve()
            if target not in path.parents or not item.isfile():
                raise ValueError("Unexpected archive member: " + item.name)
            if item.name not in read(root / "runtimes/prose-files.json"):
                raise ValueError("Unknown runtime file: " + item.name)
            expected = read(root / "runtimes/prose-files.json")[item.name]
            if path.is_file() and sha(path) == expected:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(item)
            with path.open("wb") as output:
                shutil.copyfileobj(stream, output)
            if sha(path) != expected:
                raise ValueError("PROSE runtime checksum mismatch: " + item.name)
    for image in bundle['images'].values():
        resolve_image(root, image)
    print("Runtime bundle loaded and verified.")
