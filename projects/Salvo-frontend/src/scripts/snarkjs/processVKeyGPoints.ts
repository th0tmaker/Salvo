//src/scripts/snarkjs/processVKeyGPoints.ts

/* eslint-disable @typescript-eslint/no-explicit-any */
import { getABIEncodedValue } from '@algorandfoundation/algokit-utils/types/app-arc56'
import { consoleLogger } from '@algorandfoundation/algokit-utils/types/logging'
import { bytesToHex } from 'algosdk'
import * as snarkjs from 'snarkjs'
import { APP_SPEC } from '../../contracts/PlonkVerifierWithLogs'
import { loadZKeyFromPath } from '../../utils/general/loadData'
import { getCurveFromName } from '../../utils/snarkjs/curves'

export type VerificationKey = {
  qm: Uint8Array
  ql: Uint8Array
  qr: Uint8Array
  qo: Uint8Array
  qc: Uint8Array
  s1: Uint8Array
  s2: Uint8Array
  s3: Uint8Array
  power: bigint
  nPublic: bigint
  k1: bigint
  k2: bigint
  x_2: Uint8Array
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

/**
 * Serializes selected verification key (vKey) points from a zk-SNARK `.zkey` file
 * into a base64-encoded JSON payload. This makes it easier to transport the
 * elliptic curve points in a consistent binary format.
 *
 * @param zKey - The compiled proving/verifying key artifact from snarkjs
 * @param curve - The elliptic curve implementation (must support G1 and G2 ops)
 * @returns A JSON string containing serialized uncompressed curve points
 */
export async function serializeVKeyPoints(zKey: snarkjs.ZKArtifact, curve: any): Promise<VerificationKey> {
  // Log for user clarity sake
  consoleLogger.info('Serializing verification key G points data...')
  // Export the verification key from the zKey file using snarkjs API
  const vKey = await snarkjs.zKey.exportVerificationKey(zKey, console)

  // Step 1: Process G1 points (8 separate points in the verification key)
  // ;['Qm', 'Ql', 'Qr', 'Qo', 'Qc', 'S1', 'S2', 'S3'].forEach((pointName) => {
  //   const point = curve.G1.fromObject(convertStringFieldsToBigInt(vKey[pointName]))
  //   const abc = convertStringFieldsToBigInt(vKey[pointName])
  //   consoleLogger.info(JSON.stringify(abc, (_, v) => (typeof v === 'bigint' ? v.toString() : v), 2))
  //   consoleLogger.info(point)
  //   vKey[`${pointName}Bytes`] = curve.G1.toUncompressed(point)
  // })

  // // Step 2: Process the G2 point (X_2)
  // const x2Point = curve.G2.fromObject(convertStringFieldsToBigInt(vKey.X_2))
  // const x2Uncompressed = curve.G2.toUncompressed(x2Point)

  // // Rearrange: [x1, x0, y1, y0] -> [x0, x1, y0, y1]
  // const x1 = x2Uncompressed.subarray(0, 48)
  // const x0 = x2Uncompressed.subarray(48, 96)
  // const y1 = x2Uncompressed.subarray(96, 144)
  // const y0 = x2Uncompressed.subarray(144, 192)

  // const x2Bytes = new Uint8Array(192)
  // x2Bytes.set(x0, 0)
  // x2Bytes.set(x1, 48)
  // x2Bytes.set(y0, 96)
  // x2Bytes.set(y1, 144)

  ;['Ql', 'Qr', 'Qo', 'Qm', 'Qc', 'S1', 'S2', 'S3'].forEach((p) => {
    stringValuesToBigints(vKey[p])
    const point = curve.G1.fromObject(vKey[p])
    vKey[`${p}Bytes`] = curve.G1.toUncompressed(point)
  })

  stringValuesToBigints(vKey.X_2)
  const x2Point = curve.G2.fromObject(vKey.X_2)
  const x2Uncompressed = curve.G2.toUncompressed(x2Point)

  const x1 = x2Uncompressed.subarray(0, 48)
  const x0 = x2Uncompressed.subarray(48, 96)
  const y1 = x2Uncompressed.subarray(96, 144)
  const y0 = x2Uncompressed.subarray(144, 192)

  const x2Bytes = new Uint8Array(192)
  x2Bytes.set(x0, 0)
  x2Bytes.set(x1, 48)
  x2Bytes.set(y0, 96)
  x2Bytes.set(y1, 144)

  // // Step 3: Combine all serialized G points into single buffer (768 bytes total)
  // const allPoints = [
  //   vKey.QmBytes, // 96 bytes
  //   vKey.QlBytes, // 96 bytes
  //   vKey.QrBytes, // 96 bytes
  //   vKey.QoBytes, // 96 bytes
  //   vKey.QcBytes, // 96 bytes
  //   vKey.S1Bytes, // 96 bytes
  //   vKey.S2Bytes, // 96 bytes
  //   vKey.S3Bytes, // 96 bytes
  //   x2Bytes, // 192 bytes
  // ]
  // const abiTypeStr = '(byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],byte[96],uint64,uint64,uint64,uint64,byte[192])'
  // const abiType = ABIType.from(abiTypeStr)
  // // Prepare your data in the correct order and type
  // const tupleValue = [
  //   vKey.power, // Make sure this is a BigInt or number as required
  //   vKey.nPublic, // Make sure this is a BigInt or number as required
  //   vKey.QmBytes,
  //   vKey.QlBytes,
  //   vKey.QrBytes,
  //   vKey.QoBytes,
  //   vKey.QcBytes,
  //   vKey.S1Bytes,
  //   vKey.S2Bytes,
  //   vKey.S3Bytes,
  //   BigInt(vKey.k1),
  //   BigInt(vKey.k2),
  //   x2Bytes,
  // ]
  // const encoded = abiType.encode(tupleValue)
  // const blabla = bytesToHex(encoded)

  // console.log(`blabla: ${blabla}`)
  // console.log('Raw X2:', Buffer.from(x2Uncompressed))
  // console.log('Reordered X2:', Buffer.from(x2Bytes))

  // // Pack into a single byte array
  // const buffer = new Uint8Array(960) // 8 × 96 + 192 = 960 bytes
  // let offset = 0
  // for (const pointBytes of allPoints) {
  //   buffer.set(pointBytes, offset)
  //   offset += pointBytes.length
  // }

  // // console.log(Buffer.from(allPoints.concat(scalarBytes, x2Bytes)).toString('hex'))

  // consoleLogger.info(buffer.toString())
  // // Step 4: Create JSON payload metadata
  // const payload = {
  //   app: 'salvo',
  //   version: '1.0',
  //   timestamp: new Date().toISOString(),
  //   concern: 'ZK circuit serialized verification key G points data',
  //   curve: 'bls12381',
  //   data: bytesToBase64(buffer),
  // }

  // Return JSON string
  // return JSON.stringify(payload, null, 2)

  return {
    power: vKey.power,
    nPublic: vKey.nPublic,
    ql: vKey.QlBytes,
    qr: vKey.QrBytes,
    qo: vKey.QoBytes,
    qm: vKey.QmBytes,
    qc: vKey.QcBytes,
    s1: vKey.S1Bytes,
    s2: vKey.S2Bytes,
    s3: vKey.S3Bytes,
    k1: BigInt(vKey.k1),
    k2: BigInt(vKey.k2),
    x_2: x2Bytes,
  }
}

/**
 * Loads the `.zkey` file from a given path, extracts its verification key (vKey),
 * serializes its elliptic curve points into an uncompressed format, and exports
 * the result as a JSON payload.
 *
 * This function is browser-friendly (uses `fetch` to load the `.zkey`) and * leverages `snarkjs` for BLS12-381 curve operations.
 *
 * @param zKeyPath - Path to the `.zkey` file (can be overridden by env variable or default)
 * @returns A JSON string containing uncompressed verification key points
 */
export async function getVKeyGPoints(zKeyPath: string): Promise<string> {
  // Try block
  try {
    // Use provided path or default to environment variable or fallback
    const finalZKeyPath = zKeyPath || import.meta.env?.VITE_ZKEY_PATH || 'public/main.zkey'
    // consoleLogger.info(`Loading zKey file from: ${finalZKeyPath}`)

    // Step 1: Load the zKey binary file as Uint8Array
    const zKey = await loadZKeyFromPath(import.meta.env?.VITE_ZKEY_PATH)

    // Step 2: Get the elliptic curve (BLS12-381) used for zk-SNARKs
    const curve = await getCurveFromName('bls12381')

    // Step 3: Serialize verification key points (G1 + G2) into uncompressed byte form
    // const jsonPayload = await serializeVKeyPoints(zKey, curve)

    const vkey = await serializeVKeyPoints(zKey, curve)
    const enc = getABIEncodedValue(vkey, 'VerificationKey', APP_SPEC.structs)

    // Step 4: Return the JSON payload string
    return bytesToHex(enc)
    // Catch error if method fails
  } catch (error) {
    consoleLogger.error('Error! Failed to export verification key points:', error)
    throw error
  }
}
