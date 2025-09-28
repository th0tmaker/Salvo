import base64
import json
from logging import Logger
from pathlib import Path

from algokit_utils import StructField, get_abi_encoded_value

# Setup paths
APP_DIR = Path(__file__).parent.parent
ARTIFACTS_DIR = APP_DIR / "circuits" / "turn_validator" / "artifacts"
VKEY_PATH = ARTIFACTS_DIR / "verification_key.json"

FRONTEND_DIR = APP_DIR.parent / "Salvo-frontend"


def get_root_of_unity(logger: Logger) -> str:
    # Load JSON
    with open(ARTIFACTS_DIR / "verification_key.json") as f:
        vkey_json = json.load(f)
    logger.info(list(int(vkey_json["w"]).to_bytes(32, byteorder="big")))
    logger.info(len(int(vkey_json["w"]).to_bytes(32, byteorder="big").hex()))
    # logger.info(len(int(vkey_json["Qm"]).to_bytes(96, byteorder="big").hex()))
    # logger.info(int(vkey_json["Qm"][0]))
    # logger.info(int(vkey_json["Qm"][0]).to_bytes(32, byteorder="big"))
    logger.info(FRONTEND_DIR)

    return int(vkey_json["w"]).to_bytes(32, byteorder="big").hex()


def encode_vkey(logger: Logger) -> str:
    # Load the verification key JSON (standard snarkjs format)
    with open(ARTIFACTS_DIR / "verification_key.json") as f:
        vkey_json = json.load(f)

    # Load the vkey points JSON (your custom format with base64 encoded points)
    with open(ARTIFACTS_DIR / "vkey_points.json") as f:
        vkey_points_json = json.load(f)

    # Decode the base64 encoded curve points
    vkey_points_bytes = base64.b64decode(vkey_points_json["vKeyPointsUncompressed"])

    logger.info(f"Loaded vkey_points_bytes length: {len(vkey_points_bytes)} bytes")

    # Verify expected length: 8 * G1(96) + 1 * G2(192) = 768 + 192 = 960 bytes
    if len(vkey_points_bytes) != 960:
        raise ValueError(f"Expected 960 bytes, got {len(vkey_points_bytes)} bytes")

    # Define the ABI struct
    vkey_fields = [
        StructField(name="Qm", type="byte[96]"),
        StructField(name="Ql", type="byte[96]"),
        StructField(name="Qr", type="byte[96]"),
        StructField(name="Qo", type="byte[96]"),
        StructField(name="Qc", type="byte[96]"),
        StructField(name="S1", type="byte[96]"),
        StructField(name="S2", type="byte[96]"),
        StructField(name="S3", type="byte[96]"),
        StructField(name="power", type="uint64"),
        StructField(name="nPublic", type="uint64"),
        StructField(name="k1", type="uint64"),
        StructField(name="k2", type="uint64"),
        StructField(name="X_2", type="byte[192]"),
    ]

    structs = {"VerificationKey": vkey_fields}

    # Extract G1 points (8 points, 96 bytes each)
    point_size = 96
    g1_points = ["Qm", "Ql", "Qr", "Qo", "Qc", "S1", "S2", "S3"]

    vkey_points = {}
    for i, point in enumerate(g1_points):
        start = i * point_size
        end = start + point_size
        vkey_points[point] = vkey_points_bytes[start:end]
        logger.debug(f"Extracted {point}: bytes {start}-{end}")

    # Extract G2 point (X_2) - last 192 bytes
    x2_start = 8 * point_size  # 768
    vkey_points["X_2"] = vkey_points_bytes[x2_start : x2_start + 192]
    logger.debug(f"Extracted X_2: bytes {x2_start}-{x2_start + 192}")

    # Get scalar values from verification key JSON
    # These come from the standard snarkjs verification key format
    try:
        power = int(vkey_json["power"])
        n_public = int(vkey_json["nPublic"])
        k1 = int(vkey_json["k1"])
        k2 = int(vkey_json["k2"])
    except (KeyError, ValueError) as e:
        logger.error(f"Error extracting scalar values from vkey_json: {e}")
        raise

    # Build the struct data with correct byte encoding
    vkey_bytes = {
        "Qm": vkey_points["Qm"],
        "Ql": vkey_points["Ql"],
        "Qr": vkey_points["Qr"],
        "Qo": vkey_points["Qo"],
        "Qc": vkey_points["Qc"],
        "S1": vkey_points["S1"],
        "S2": vkey_points["S2"],
        "S3": vkey_points["S3"],
        "power": power,
        "nPublic": n_public,
        "k1": k1,
        "k2": k2,
        "X_2": vkey_points["X_2"],
    }

    logger.info("Verification key components:")
    logger.info(f"  Power: {power}")
    logger.info(f"  nPublic: {n_public}")
    logger.info(f"  k1: {k1}")
    logger.info(f"  k2: {k2}")
    logger.info(f"  G1 points: {len(g1_points)} points, {point_size} bytes each")
    logger.info(f"  G2 point (X_2): {len(vkey_points['X_2'])} bytes")

    # Validate byte array lengths
    for field_name, field_value in vkey_bytes.items():
        if isinstance(field_value, bytes):
            expected_length = {
                "Qm": 96,
                "Ql": 96,
                "Qr": 96,
                "Qo": 96,
                "Qc": 96,
                "S1": 96,
                "S2": 96,
                "S3": 96,
                "power": 8,
                "nPublic": 8,
                "k1": 8,
                "k2": 8,
                "X_2": 192,
            }
            if field_name in expected_length:
                actual_length = len(field_value)
                if actual_length != expected_length[field_name]:
                    raise ValueError(
                        f"Field {field_name}: expected {expected_length[field_name]} bytes, "
                        f"got {actual_length} bytes"
                    )

    # Encode the struct using Algorand ABI
    try:
        encoded = get_abi_encoded_value(vkey_bytes, "VerificationKey", structs)
        logger.info(f"Successfully encoded verification key: {len(encoded)} bytes")
        return encoded.hex()
    except Exception as e:
        logger.error(f"Failed to encode verification key: {e}")
        raise
