"""Run with Blender --background FILE --python inspect_scene.py -- --report FILE.

Reads current scene data without saving or modifying the blend. This is an
inventory, not evaluated collision, visual-quality, or simulation validation.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy


def source_record(use_hash):
    source = bpy.data.filepath
    if not source:
        return {"path": None, "saved": False}
    path = Path(source)
    record = {"path": str(path), "saved": True, "bytes": path.stat().st_size}
    if use_hash:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(block)
        record["sha256"] = digest.hexdigest()
    return record


def resource_record(kind, block):
    raw = str(getattr(block, "filepath", "") or "")
    record = {"kind": kind, "name": block.name, "path": raw}
    if getattr(block, "packed_file", None) or len(getattr(block, "packed_files", ())):
        record["status"] = "packed"
    elif raw == "<builtin>" or getattr(block, "source", "") in {"GENERATED", "VIEWER"}:
        record["status"] = "builtin_or_generated"
    elif not raw:
        record["status"] = "no_external_path"
    else:
        resolved = bpy.path.abspath(raw, library=getattr(block, "library", None))
        record["resolved_path"] = resolved
        if any(token in raw for token in ("<UDIM>", "<UVTILE>", "#", "%")):
            record["status"] = "pattern_not_expanded"
        else:
            record["status"] = "exists" if Path(resolved).is_file() else "missing"
    return record


def camera_record(obj):
    camera = obj.data
    return {
        "object": obj.name, "type": camera.type,
        "world_matrix": [list(row) for row in obj.matrix_world],
        "lens_mm": camera.lens, "sensor_width_mm": camera.sensor_width,
        "sensor_height_mm": camera.sensor_height, "sensor_fit": camera.sensor_fit,
        "angle_x_rad": camera.angle_x, "angle_y_rad": camera.angle_y,
        "clip_start": camera.clip_start, "clip_end": camera.clip_end,
        "dof_enabled": camera.dof.use_dof,
    }


def exclusions(layer_collection, parent=""):
    path = parent + "/" + layer_collection.name
    out = [path] if layer_collection.exclude or layer_collection.hide_viewport else []
    for child in layer_collection.children:
        out.extend(exclusions(child, path))
    return out


def inspect(limit, hash_source):
    scene = bpy.context.scene
    objects = sorted(scene.objects, key=lambda obj: obj.name)
    ids = defaultdict(list)
    details = []
    for obj in objects:
        stable_id = obj.get("stable_id")
        if stable_id is not None and str(stable_id):
            ids[str(stable_id)].append(obj.name)
        if limit and len(details) >= limit:
            continue
        details.append({
            "name": obj.name, "type": obj.type, "stable_id": str(stable_id) if stable_id is not None else None,
            "world_matrix": [list(row) for row in obj.matrix_world],
            "dimensions_local_units": list(obj.dimensions),
            "parent": obj.parent.name if obj.parent else None,
            "collections": [col.name for col in obj.users_collection],
            "hide_render": obj.hide_render, "hide_viewport": obj.hide_viewport,
            "instance_type": obj.instance_type,
            "instance_collection": obj.instance_collection.name if obj.instance_collection else None,
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "constraints": [con.type for con in obj.constraints],
            "modifiers": [mod.type for mod in obj.modifiers],
        })
    resources = []
    for kind, blocks in (("image", bpy.data.images), ("font", bpy.data.fonts),
                         ("linked_library", bpy.data.libraries),
                         ("movieclip", bpy.data.movieclips), ("sound", bpy.data.sounds)):
        resources.extend(resource_record(kind, block) for block in blocks)
    render = scene.render
    samples = {}
    for owner_name in ("cycles", "eevee"):
        owner = getattr(scene, owner_name, None)
        if owner is not None:
            samples[owner_name] = {key: getattr(owner, key) for key in
                ("samples", "preview_samples", "taa_render_samples", "taa_samples", "use_denoising")
                if hasattr(owner, key)}
    return {
        "blender_version": bpy.app.version_string,
        "source": source_record(hash_source),
        "scope": "Original datablocks at the loaded frame; no simulation, collision or visual validation.",
        "scene": scene.name, "all_scenes": [item.name for item in bpy.data.scenes],
        "units": {"system": scene.unit_settings.system, "scale_length": scene.unit_settings.scale_length,
                  "length_unit": scene.unit_settings.length_unit},
        "frame": scene.frame_current, "frame_start": scene.frame_start, "frame_end": scene.frame_end,
        "fps": render.fps, "fps_base": render.fps_base, "actual_fps": render.fps / render.fps_base,
        "render": {
            "engine": render.engine, "width": render.resolution_x, "height": render.resolution_y,
            "percentage": render.resolution_percentage,
            "effective_size": [int(render.resolution_x * render.resolution_percentage / 100),
                               int(render.resolution_y * render.resolution_percentage / 100)],
            "output_path": render.filepath, "format": render.image_settings.file_format,
            "view_transform": scene.view_settings.view_transform,
            "exposure": scene.view_settings.exposure, "look": scene.view_settings.look,
            "sampling_properties_available": samples,
            "motion_blur": getattr(render, "use_motion_blur", None),
        },
        "active_camera": scene.camera.name if scene.camera else None,
        "cameras": [camera_record(obj) for obj in objects if obj.type == "CAMERA"],
        "counts": {"scene_objects": len(objects), "object_types": dict(Counter(obj.type for obj in objects)),
                   "mesh_datablocks": len(bpy.data.meshes), "materials": len(bpy.data.materials),
                   "unique_mesh_vertices": sum(len(mesh.vertices) for mesh in bpy.data.meshes),
                   "unique_mesh_polygons": sum(len(mesh.polygons) for mesh in bpy.data.meshes)},
        "objects": details, "object_records_truncated": len(details) < len(objects),
        "duplicate_stable_ids": {key: names for key, names in ids.items() if len(names) > 1},
        "resources": resources, "missing_resources": [item for item in resources if item["status"] == "missing"],
        "unexpanded_resource_patterns": [item for item in resources if item["status"] == "pattern_not_expanded"],
        "actions": [{"name": action.name, "slots": [{"identifier": slot.identifier,
                     "target_id_type": getattr(slot, "target_id_type", None)}
                     for slot in getattr(action, "slots", ())]} for action in bpy.data.actions],
        "view_layers": [{"name": layer.name, "excluded_or_hidden_collections": exclusions(layer.layer_collection)}
                        for layer in scene.view_layers],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--object-limit", type=int, default=200, help="Object records; 0 means unlimited.")
    parser.add_argument("--hash-source", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    if args.object_limit < 0:
        parser.error("--object-limit must be nonnegative")
    result = inspect(args.object_limit, args.hash_source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SCENE_INVENTORY_WRITTEN", str(args.report), flush=True)


if __name__ == "__main__":
    main()
