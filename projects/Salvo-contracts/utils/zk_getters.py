import base64
import json
from dataclasses import asdict
from logging import Logger
from pathlib import Path

from algokit_utils import get_abi_encoded_value

from smart_contracts.artifacts.plonk_verifier.plonk_verifier_client import APP_SPEC
from utils.zk_models import LagrangeWitness, Proof, VerificationKey

# Setup paths
APP_DIR = Path(__file__).parent.parent
ARTIFACTS_DIR = APP_DIR / "circuits" / "main" / "artifacts"
VKEY_PATH = ARTIFACTS_DIR / "verification_key.json"

FRONTEND_DIR = APP_DIR.parent / "Salvo-frontend"


# Get ZK circuit Lagrange witness
def get_zk_lagrange_witness() -> LagrangeWitness:
    # Load raw data from ZK circuit public JSON file
    with open(ARTIFACTS_DIR / "lagrange_witness.json") as f:
        lw_json = json.load(f)

    return LagrangeWitness(
        l=lw_json["l"],
        xin=lw_json["xin"],
        zh=lw_json["zh"],
    )


# Get ZK circuit public signals
def get_zk_public_signals() -> list[int]:
    # Load raw data from ZK circuit public JSON file
    with open(ARTIFACTS_DIR / "public.json") as f:
        public_json = json.load(f)

    # Iterate through the public_json file and return a list of each element as an int
    return [int(i) for i in public_json]


# Get ZK circuit verification key `root of unity` field
def get_zk_root_of_unity_as_bytes() -> bytes:
    # Load raw data from ZK circuit verification key JSON file
    with open(ARTIFACTS_DIR / "verification_key.json") as f:
        vkey_json = json.load(f)

    # Convert `root of unity` value to big endian bytes of length 32
    return int(vkey_json["w"]).to_bytes(32, byteorder="big")


# Get ZK circuit verification key data
def get_zk_vkey(logger: Logger) -> VerificationKey:
    # Load raw data from ZK circuit verification key JSON file
    with open(ARTIFACTS_DIR / "verification_key.json") as f:
        vkey_json = json.load(f)

    # Load serialized data from ZK circuit verification key curve points payload JSON file
    with open(ARTIFACTS_DIR / "vkey_gpoints_payload.json") as f:
        vkey_points_json = json.load(f)

    # Decode the base64 encoded verifcation key curve points data
    vkey_points_bytes = base64.b64decode(vkey_points_json["data"])

    # Verify `vkey_points_bytes` expected length: 8 * G1(96) + 1 * G2(192) = 768 + 192 = 960 bytes
    if len(vkey_points_bytes) != 960:
        raise ValueError(
            f"Expected 960 bytes, but got {len(vkey_points_bytes)} bytes instead"
        )

    # Define verification key G1 points and length (8 points, 96 bytes each)
    point_size = 96
    g1_labels = ["Qm", "Ql", "Qr", "Qo", "Qc", "S1", "S2", "S3"]

    # Iterate over all G1 labels and slice out their corresponding 96-byte segments
    vkey_g1_points = {
        label: vkey_points_bytes[i * point_size : (i + 1) * point_size]
        for i, label in enumerate(g1_labels)
    }

    # Slice the G2 point (X_2) - last 192 bytes
    x2_start = 8 * point_size  # 768
    vkey_g2_point = vkey_points_bytes[x2_start : x2_start + 192]

    x1 = vkey_g2_point[0:48]
    x0 = vkey_g2_point[48:96]
    y1 = vkey_g2_point[96:144]
    y0 = vkey_g2_point[144:192]

    logger.info(x1)
    logger.info(x0)
    logger.info(y1)
    logger.info(y0)

    # Extract the smaller-sized scalar values as standard integers from the raw json data
    try:
        scalars = {
            "power": int(vkey_json["power"]),
            "nPublic": int(vkey_json["nPublic"]),
            "k1": int(vkey_json["k1"]),
            "k2": int(vkey_json["k2"]),
        }
    except KeyError as e:
        raise KeyError(f"Missing scalar value in vkey JSON: {e}") from e
    except ValueError as e:
        raise ValueError(f"Invalid scalar value in vkey JSON: {e}") from e

    # Build an instance of the VerificationKey class
    vk = VerificationKey(
        **vkey_g1_points,  # expands Qm, Ql, Qr, Qo, Qc, S1, S2, S3,
        **scalars,  # expands power, nPublic, k1, k2
        X_2=vkey_g2_point,  # X_2
    )

    # Return a new instance of the Proof data class
    return vk


# Encode ZK circuit proof data for LWC contract compatibility
def get_zk_proof() -> Proof:
    # Load raw data from ZK circuit proof JSON file
    with open(ARTIFACTS_DIR / "proof.json") as f:
        proof_json = json.load(f)

    # Load serialized data from ZK circuit proof payload JSON file
    with open(ARTIFACTS_DIR / "proof_payload.json") as f:
        proof_payload_json = json.load(f)

    # Decode the base64 encoded proof data
    proof_bytes = base64.b64decode(proof_payload_json["data"])

    # Verify `proof_bytes` expected length: 9 * G1(96) + 6 * fEval(32) = 864 + 192 = 1056 bytes
    if len(proof_bytes) != 1056:
        raise ValueError(
            f"Expected 1056 bytes, but got {len(proof_bytes)} bytes instead"
        )

    # Define proof G1 labels and length (9 points, 96 bytes each)
    point_size = 96
    g1_labels = ["A", "B", "C", "Z", "T1", "T2", "T3", "Wxi", "Wxiw"]

    # Iterate over all G1 points and slice out their corresponding 96-byte segments
    proof_g1_points: dict[str, bytes] = {
        label: proof_bytes[i * point_size : (i + 1) * point_size]
        for i, label in enumerate(g1_labels)
    }

    # NOTE: EVAL_X is 32 byte array, go int.from_bytes() before assigning their values to PROOF
    # Extract the smaller-sized scalar values as standard integers from the raw json data
    try:
        scalars = {
            key: int(proof_json[key])
            for key in ["eval_a", "eval_b", "eval_c", "eval_s1", "eval_s2", "eval_zw"]
        }
    except KeyError as e:
        raise KeyError(f"Missing scalar value in proof JSON: {e}") from e
    except ValueError as e:
        raise ValueError(f"Invalid scalar value in proof JSON: {e}") from e

    # Return a new instance of the Proof data class
    return Proof(
        **proof_g1_points,  # expands A, B, C, Z, T1, T2, T3, Wxi, Wxiw
        **scalars,  # expands eval_a, eval_b, eval_c, eval_s1, eval_s2, eval_zw
    )


# Get ZK circuit verification key data as bytes
def get_zk_vkey_as_bytes(vk: VerificationKey, logger: Logger) -> bytes:
    logger.info(
        get_abi_encoded_value(asdict(vk), "VerificationKey", APP_SPEC.structs).hex()
    )
    return get_abi_encoded_value(asdict(vk), "VerificationKey", APP_SPEC.structs)
    # return (
    #     vk.Qm  # 96 bytes
    #     + vk.Ql  # 96 bytes
    #     + vk.Qr  # 96 bytes
    #     + vk.Qo  # 96 bytes
    #     + vk.Qc  # 96 bytes
    #     + vk.S1  # 96 bytes
    #     + vk.S2  # 96 bytes
    #     + vk.S3  # 96 bytes
    #     + vk.power.to_bytes(8, "big")  # 8 bytes
    #     + vk.nPublic.to_bytes(8, "big")  # 8 bytes
    #     + vk.k1.to_bytes(8, "big")  # 8 bytes
    #     + vk.k2.to_bytes(8, "big")  # 8 bytes
    #     + vk.X_2  # 192 bytes
    # )  # Total length: 992 bytes


# export function encodeVk(
#   vkey: VerificationKey,
#   appSpec: Arc56Contract,
# ): Uint8Array {
#   return getABIEncodedValue(vkey, "VerificationKey", appSpec.structs);
# }


# Get ZK circuit verification key data as bytes
def get_zk_proof_as_bytes(proof: Proof) -> bytes:
    return (
        proof.A  # 96 bytes
        + proof.B  # 96 bytes
        + proof.C  # 96 bytes
        + proof.Z  # 96 bytes
        + proof.T1  # 96 bytes
        + proof.T2  # 96 bytes
        + proof.T3  # 96 bytes
        + proof.Wxi  # 96 bytes
        + proof.Wxiw  # 96 bytes
        + proof.eval_a.to_bytes(32, "big")  # 32 bytes
        + proof.eval_b.to_bytes(32, "big")  # 32 bytes
        + proof.eval_c.to_bytes(32, "big")  # 32 bytes
        + proof.eval_s1.to_bytes(32, "big")  # 32 bytes
        + proof.eval_s2.to_bytes(32, "big")  # 32 bytes
        + proof.eval_zw.to_bytes(32, "big")  # 32 bytes
    )  # Total length: 1056 bytes
