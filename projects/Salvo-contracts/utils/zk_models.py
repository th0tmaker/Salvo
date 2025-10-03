from dataclasses import dataclass


# Class for ZK circuit verification_key.json file data
@dataclass
class VerificationKey:
    Qm: bytes  # 96 bytes
    Ql: bytes  # 96 bytes
    Qr: bytes  # 96 bytes
    Qo: bytes  # 96 bytes
    Qc: bytes  # 96 bytes
    S1: bytes  # 96 bytes
    S2: bytes  # 96 bytes
    S3: bytes  # 96 bytes
    power: int  # uint64
    nPublic: int  # uint64
    k1: int  # uint64
    k2: int  # uint64
    X_2: bytes  # 192 bytes


# Class for ZK circuit proof.json file data
@dataclass
class Proof:
    A: bytes  # 96 bytes
    B: bytes  # 96 bytes
    C: bytes  # 96 bytes
    Z: bytes  # 96 bytes
    T1: bytes  # 96 bytes
    T2: bytes  # 96 bytes
    T3: bytes  # 96 bytes
    Wxi: bytes  # 96 bytes
    Wxiw: bytes  # 96 bytes
    eval_a: int  # uint256
    eval_b: int  # uint256
    eval_c: int  # uint256
    eval_s1: int  # uint256
    eval_s2: int  # uint256
    eval_zw: int  # uint256


# Class for ZK circuit lagrange_witness.json file data
@dataclass
class LagrangeWitness:
    l: list[int]  # uint256[]
    xin: int  # uint256
    zh: int  # uint256
