import os
import json
import struct


class AssetMetadataService:

    @staticmethod
    def extract_metadata(file_path, original_filename=None):
        extension = os.path.splitext(file_path)[1].lower()

        metadata = {
            "original_filename": original_filename,
            "extension": extension,
            "file_size_bytes": os.path.getsize(file_path),
            "interpretable": True,
            "objects": [],
            "meshes": [],
            "materials": [],
            "object_count": 0,
            "mesh_count": 0,
            "material_count": 0
        }

        try:
            if extension == ".obj":
                return AssetMetadataService._extract_obj_metadata(file_path, metadata)

            if extension == ".gltf":
                return AssetMetadataService._extract_gltf_metadata(file_path, metadata)

            if extension == ".glb":
                return AssetMetadataService._extract_glb_metadata(file_path, metadata)

            metadata["interpretable"] = False
            metadata["error"] = "Unsupported format for metadata extraction"
            return metadata

        except Exception as e:
            metadata["interpretable"] = False
            metadata["error"] = str(e)
            return metadata

    @staticmethod
    def _extract_obj_metadata(file_path, metadata):
        objects = set()
        vertex_count = 0
        face_count = 0

        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                if line.startswith("o ") or line.startswith("g "):
                    objects.add(line.strip().split(maxsplit=1)[1])
                elif line.startswith("v "):
                    vertex_count += 1
                elif line.startswith("f "):
                    face_count += 1

        metadata["objects"] = list(objects)
        metadata["object_count"] = len(objects)
        metadata["vertex_count"] = vertex_count
        metadata["face_count"] = face_count
        return metadata

    @staticmethod
    def _extract_gltf_metadata(file_path, metadata):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return AssetMetadataService._extract_from_gltf_json(data, metadata)

    @staticmethod
    def _extract_glb_metadata(file_path, metadata):
        with open(file_path, "rb") as file:
            magic, version, length = struct.unpack("<4sII", file.read(12))

            if magic != b"glTF":
                metadata["interpretable"] = False
                metadata["error"] = "Invalid GLB file"
                return metadata

            chunk_length, chunk_type = struct.unpack("<I4s", file.read(8))

            if chunk_type != b"JSON":
                metadata["interpretable"] = False
                metadata["error"] = "GLB JSON chunk not found"
                return metadata

            json_chunk = file.read(chunk_length).decode("utf-8")
            data = json.loads(json_chunk)

        return AssetMetadataService._extract_from_gltf_json(data, metadata)

    @staticmethod
    def _extract_from_gltf_json(data, metadata):
        nodes = data.get("nodes", [])
        meshes = data.get("meshes", [])
        materials = data.get("materials", [])

        metadata["objects"] = [
            node.get("name", f"Node_{index}")
            for index, node in enumerate(nodes)
        ]

        metadata["meshes"] = [
            mesh.get("name", f"Mesh_{index}")
            for index, mesh in enumerate(meshes)
        ]

        metadata["materials"] = [
            material.get("name", f"Material_{index}")
            for index, material in enumerate(materials)
        ]

        metadata["object_count"] = len(nodes)
        metadata["mesh_count"] = len(meshes)
        metadata["material_count"] = len(materials)

        return metadata