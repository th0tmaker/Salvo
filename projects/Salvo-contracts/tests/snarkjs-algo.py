import subprocess

FRONTEND_PATH = "../Salvo-frontend"  # adjust path if needed


def snarkjs_verify(vkey_path, proof_path, public_path):
    result = subprocess.run(
        ["npx", "snarkjs", "plonk", "verify", vkey_path, proof_path, public_path],
        cwd=FRONTEND_PATH,  # run inside frontend folder
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()
