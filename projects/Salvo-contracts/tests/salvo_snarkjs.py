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


def encode_proof(logger: Logger) -> str:
    # Load the serialized proof data JSON file
    with open(ARTIFACTS_DIR / "proof.json") as f:
        proof_json = json.load(f)

    with open(ARTIFACTS_DIR / "proof_payload.json") as f:
        proof_payload_json = json.load(f)

    # Decode the base64 encoded curve points
    proof_payload_bytes = base64.b64decode(proof_payload_json["data"])

    # Verify expected length: 9 * G1(96) + 6 * fEval(32) = 864 + 192 = 1056 bytes
    if len(proof_payload_bytes) != 1056:
        raise ValueError(f"Expected 1056 bytes, got {len(proof_payload_bytes)} bytes")

    # Define the ABI struct
    proof_fields = [
        StructField(name="A", type="byte[96]"),
        StructField(name="B", type="byte[96]"),
        StructField(name="C", type="byte[96]"),
        StructField(name="Z", type="byte[96]"),
        StructField(name="T1", type="byte[96]"),
        StructField(name="T2", type="byte[96]"),
        StructField(name="T3", type="byte[96]"),
        StructField(name="Wxi", type="byte[96]"),
        StructField(name="Wxiw", type="byte[96]"),
        StructField(name="eval_a", type="uint256"),
        StructField(name="eval_b", type="uint256"),
        StructField(name="eval_c", type="uint256"),
        StructField(name="eval_s1", type="uint256"),
        StructField(name="eval_s2", type="uint256"),
        StructField(name="eval_zw", type="uint256"),
    ]

    # Extract G1 points (8 points, 96 bytes each)
    point_size = 96
    g1_points = ["A", "B", "C", "Z", "T1", "T2", "T3", "Wxi", "Wxiw"]

    proof_g1_points = {}
    for i, point in enumerate(g1_points):
        start = i * point_size
        end = start + point_size
        proof_g1_points[point] = proof_payload_bytes[start:end]
        logger.debug(f"Extracted {point}: bytes {start}-{end}")

    # Get scalar values from proof JSON
    # These come from the standard snarkjs verification key format
    try:
        eval_a = int(proof_json["eval_a"])
        eval_b = int(proof_json["eval_b"])
        eval_c = int(proof_json["eval_c"])
        eval_s1 = int(proof_json["eval_s1"])
        eval_s2 = int(proof_json["eval_s2"])
        eval_zw = int(proof_json["eval_zw"])
    except (KeyError, ValueError) as e:
        logger.error(f"Error extracting scalar values from proof_json: {e}")
        raise

    # Build the struct data with correct byte encoding
    proof_bytes = {
        "A": proof_g1_points["A"],
        "B": proof_g1_points["B"],
        "C": proof_g1_points["C"],
        "Z": proof_g1_points["Z"],
        "T1": proof_g1_points["T1"],
        "T2": proof_g1_points["T2"],
        "T3": proof_g1_points["T3"],
        "Wxi": proof_g1_points["Wxi"],
        "Wxiw": proof_g1_points["Wxiw"],
        "eval_a": eval_a,
        "eval_b": eval_b,
        "eval_c": eval_c,
        "eval_s1": eval_s1,
        "eval_s2": eval_s2,
        "eval_zw": eval_zw,
    }

    # DEBUG
    # Validate byte array lengths
    # for field_name, field_value in proof_bytes.items():
    #     if isinstance(field_value, bytes):
    #         expected_length = {
    #             "A": 96,
    #             "B": 96,
    #             "C": 96,
    #             "Z": 96,
    #             "T1": 96,
    #             "T2": 96,
    #             "T3": 96,
    #             "Wxi": 96,
    #             "Wxiw": 96,
    #             "eval_a": 32,
    #             "eval_b": 32,
    #             "eval_c": 32,
    #             "eval_s1": 32,
    #             "eval_s2": 32,
    #             "eval_zw": 32,
    #         }
    #         if field_name in expected_length:
    #             actual_length = len(field_value)
    #             if actual_length != expected_length[field_name]:
    #                 raise ValueError(
    #                     f"Field {field_name}: expected {expected_length[field_name]} bytes, "
    #                     f"got {actual_length} bytes"
    #                 )

    # Encode the struct using Algorand ABI
    try:
        encoded = get_abi_encoded_value(proof_bytes, "Proof", {"Proof": proof_fields})
        logger.info(f"Successfully encoded verification key: {len(encoded)} bytes")
        return encoded.hex()
    except Exception as e:
        logger.error(f"Failed to encode verification key: {e}")
        raise
