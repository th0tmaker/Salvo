//src/scripts/snarkjs/processProof.ts

/* eslint-disable @typescript-eslint/no-explicit-any */
import { consoleLogger } from '@algorandfoundation/algokit-utils/types/logging'
import { bigIntToBytes, bytesToBase64, bytesToHex } from 'algosdk'
import { loadJSONFromPath } from '../../utils/general/loadData'
import { convertStringFieldsToBigInt } from '../../utils/general/parseData'

/**
 * Serializes ZK circuit proof from a `.json` file
 * into a base64-encoded JSON payload. This makes it easier to transport the
 * elliptic curve points in a consistent binary format.
 *
 * @param path - Path to the proof JSON file
 * @param curve - The BLS12-381 curve object from snarkjs
 * @returns Base64-encoded string containing all proof points and evaluations
 */
export async function serializeProof(proofPath: string, curve: any): Promise<string> {
  // Use provided path or default to environment variable or fallback
  const finalProofPath = proofPath || import.meta.env?.VITE_PROOF_PATH || 'public/proof.json'
  consoleLogger.info(`Loading proof file from: ${finalProofPath}`)

  // Step 1: Read and parse JSON - AWAIT the promise
  const rawProof = (await loadJSONFromPath(finalProofPath)) as any // Fixed: use finalProofPath

  // Step 2: Convert G1 points to uncompressed bytes
  const g1PointsNames = ['A', 'B', 'C', 'Z', 'T1', 'T2', 'T3', 'Wxi', 'Wxiw'] as const
  const g1Points: Uint8Array[] = []
  for (const name of g1PointsNames) {
    const point = curve.G1.fromObject(convertStringFieldsToBigInt(rawProof[name]))
    g1Points.push(curve.G1.toUncompressed(point)) // 96 bytes
  }

  // Step 3: Convert field evaluations to BigInt
  const evalNames = ['eval_a', 'eval_b', 'eval_c', 'eval_s1', 'eval_s2', 'eval_zw'] as const
  const evalBigInts: bigint[] = evalNames.map((field) => BigInt(rawProof[field]))

  // Step 4: Pack everything into Uint8Array
  const buffer = new Uint8Array(1056) // 9×96 + 6×32 = 1056 bytes
  let offset = 0

  for (const pointBytes of g1Points) {
    buffer.set(pointBytes, offset)
    offset += pointBytes.length
  }

  // Helper: convert BigInt → 32-byte BE
  const bigIntTo32Bytes = (n: bigint): Uint8Array => {
    const arr = new Uint8Array(32)
    let temp = n
    for (let i = 31; i >= 0; i--) {
      arr[i] = Number(temp & 0xffn)
      temp >>= 8n
    }
    return arr
  }

  const test3 = BigInt(3)
  const test3Bbytes = bigIntToBytes(test3, 32)

  const test3Bytes = bigIntTo32Bytes(test3)

  console.log(`bigIntToBytes: ${test3Bbytes}`)
  console.log(`bigIntTo32Bytes: ${test3Bytes}`)
  // Copy field evaluations
  for (const n of evalBigInts) {
    buffer.set(bigIntTo32Bytes(n), offset)
    offset += 32
  }

  console.log(`proof hex ${bytesToHex(buffer)}`)

  const abiTypeStr =
    '(byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],uint256,uint256,uint256,uint256,uint256,uint256)'

  // Step 5: Create JSON payload metadata
  const payload = {
    app: 'salvo',
    version: '1.0',
    timestamp: new Date().toISOString(),
    concern: 'ZK circuit serialized proof data',
    curve: 'bls12381',
    data: bytesToBase64(buffer),
  }

  // Return JSON string
  return JSON.stringify(payload, null, 2)
}

export type Proof = {
  a: Uint8Array
  b: Uint8Array
  c: Uint8Array
  z: Uint8Array
  t1: Uint8Array
  t2: Uint8Array
  t3: Uint8Array
  wxi: Uint8Array
  wxiw: Uint8Array
  evalA: bigint
  evalB: bigint
  evalC: bigint
  evalS1: bigint
  evalS2: bigint
  evalZw: bigint
}

function stringValuesToBigints(obj: any): any {
  for (const key in obj) {
    if (typeof obj[key] === 'string' && /^\d+$/.test(obj[key])) {
      obj[key] = BigInt(obj[key])
    } else if (typeof obj[key] === 'object' && obj[key] !== null) {
      stringValuesToBigints(obj[key])
    }
  }
}

export function encodeProof(proof: any, curve: any): Proof {
  ;['A', 'B', 'C', 'Z', 'T1', 'T2', 'T3', 'Wxi', 'Wxiw'].forEach((p) => {
    stringValuesToBigints(proof[p])
    const point = curve.G1.fromObject(proof[p])
    proof[`${p}Bytes`] = curve.G1.toUncompressed(point)
  })
  ;['eval_a', 'eval_b', 'eval_c', 'eval_s1', 'eval_s2', 'eval_zw'].forEach((p) => {
    proof[`${p}BigInt`] = BigInt(proof[p])
  })

  return {
    a: proof.ABytes,
    b: proof.BBytes,
    c: proof.CBytes,
    z: proof.ZBytes,
    t1: proof.T1Bytes,
    t2: proof.T2Bytes,
    t3: proof.T3Bytes,
    wxi: proof.WxiBytes,
    wxiw: proof.WxiwBytes,
    evalA: proof.eval_aBigInt,
    evalB: proof.eval_bBigInt,
    evalC: proof.eval_cBigInt,
    evalS1: proof.eval_s1BigInt,
    evalS2: proof.eval_s2BigInt,
    evalZw: proof.eval_zwBigInt,
  }
}

function concatProofBytes(proofko: any): string {
  const chunks: Uint8Array[] = []

  for (const key of Object.keys(proofko)) {
    const value = proofko[key]

    if (value instanceof Uint8Array) {
      chunks.push(value)
    } else if (typeof value === 'bigint') {
      // Convert BigInt to 32-byte big-endian Uint8Array
      chunks.push(bigIntToBytes(value, 32))
    } else {
      throw new Error(`Unsupported field type for proof key "${key}"`)
    }
  }

  // Compute total length
  const totalLength = chunks.reduce((sum, arr) => sum + arr.length, 0)
  const buffer = new Uint8Array(totalLength)

  // Copy chunks into the buffer
  let offset = 0
  for (const arr of chunks) {
    buffer.set(arr, offset)
    offset += arr.length
  }

  return bytesToHex(buffer)
}

export async function getProof(path: string, curve: any): Promise<Proof> {
  const response = await fetch('/proof.json')
  const proof = await response.json()
  const proofko = encodeProof(proof, curve)

  const proofHex = concatProofBytes(proofko)
  console.log('Concatenated proof hex:', proofHex)

  // Suppose proofko has fields A, B, C as Uint8Array or similar
  console.log('A bytes:', bytesToHex(proofko.a))
  console.log('B bytes:', bytesToHex(proofko.b))
  console.log('C bytes:', bytesToHex(proofko.c))
  console.log('eval_a bytes:', bytesToHex(bigIntToBytes(proofko.evalA, 32)))
  console.log('eval_b bytes:', bytesToHex(bigIntToBytes(proofko.evalB, 32)))
  console.log('eval_c bytes:', bytesToHex(bigIntToBytes(proofko.evalC, 32)))

  return encodeProof(proof, curve)
}
