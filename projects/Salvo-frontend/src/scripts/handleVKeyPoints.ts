/* eslint-disable @typescript-eslint/no-explicit-any */
import { consoleLogger } from '@algorandfoundation/algokit-utils/types/logging'
import { bytesToBase64 } from 'algosdk'
import * as snarkjs from 'snarkjs'
import { getCurveFromName } from '../utils/snarkjs/curves'

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

function convertStringFieldsToBigInt(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  for (const key in obj) {
    if (typeof obj[key] === 'string' && /^\d+$/.test(obj[key] as string)) {
      result[key] = BigInt(obj[key] as string)
    } else if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
      result[key] = convertStringFieldsToBigInt(obj[key] as Record<string, unknown>)
    } else {
      result[key] = obj[key]
    }
  }

  return result
}

/**
 * Browser-compatible function to download a file
 */
function downloadFile(content: string, filename: string, contentType: string = 'application/json') {
  const blob = new Blob([content], { type: contentType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Browser-compatible function to load a file from public folder
 */
export async function loadZKeyFromPath(path: string): Promise<Uint8Array> {
  try {
    const response = await fetch(path)
    if (!response.ok) {
      throw new Error(`Failed to fetch ${path}: ${response.status} ${response.statusText}`)
    }
    const buffer = await response.arrayBuffer()
    return new Uint8Array(buffer)
  } catch (error) {
    throw new Error(`Failed to load zKey file from ${path}: ${error}`)
  }
}

/**
 * Takes verification key curve points G1 and G2 from a zKey and uncompresses them, then
 * combines all the uncompressed curve points into a single buffer Uint8Array
 * that gets serialized into a Base64-encoded string. Finally, returns the payload as JSON string
 */
export async function serializeVKeyPoints(zKey: snarkjs.ZKArtifact, curve: any): Promise<string> {
  const vkey = await snarkjs.zKey.exportVerificationKey(zKey, console)

  // snarkjs.plonk.fullProve()

  // Process G1 points (8 points: Ql, Qr, Qo, Qm, Qc, S1, S2, S3)
  ;['Ql', 'Qr', 'Qo', 'Qm', 'Qc', 'S1', 'S2', 'S3'].forEach((pointName) => {
    convertStringFieldsToBigInt(vkey[pointName])
    const point = curve.G1.fromObject(vkey[pointName])
    vkey[`${pointName}Bytes`] = curve.G1.toUncompressed(point)
  })

  // Process G2 point (X_2)
  convertStringFieldsToBigInt(vkey.X_2)
  const x2Uncompressed = curve.G2.toUncompressed(curve.G2.fromObject(vkey.X_2))

  // Pack serialized G2 points into byte array
  const x2Bytes = new Uint8Array(192)
  x2Bytes.set(x2Uncompressed.subarray(48, 96), 0)
  x2Bytes.set(x2Uncompressed.subarray(0, 48), 48)
  x2Bytes.set(x2Uncompressed.subarray(96, 144), 96)
  x2Bytes.set(x2Uncompressed.subarray(96, 144), 144)

  // Combine all points into single buffer
  const pointParts = [
    vkey.QlBytes,
    vkey.QrBytes,
    vkey.QoBytes,
    vkey.QmBytes,
    vkey.QcBytes,
    vkey.S1Bytes,
    vkey.S2Bytes,
    vkey.S3Bytes,
    x2Bytes, // G2 point (192 bytes)
  ]

  // Pack all curve points into byte array
  const combinedUncompressedPoints = new Uint8Array(960) // 8 × G1(96) + 1 × G2(192)
  let offset = 0
  for (const pointBytes of pointParts) {
    combinedUncompressedPoints.set(pointBytes, offset)
    offset += pointBytes.length
  }

  // Create JSON payload metadata
  const payload = {
    version: '1.0',
    curve: 'bls12-381',
    vKeyPointsUncompressed: bytesToBase64(combinedUncompressedPoints),
    timestamp: new Date().toISOString(),
  }

  return JSON.stringify(payload, null, 2)
}

/**
 * Browser-compatible wrapper function that loads zKey from public folder and exports uncompressed verification key points
 */
export async function exportVKeyPoints(zKeyPath?: string, shouldDownload: boolean = true): Promise<string> {
  try {
    // Use provided path or default to environment variable or fallback
    const finalZKeyPath = zKeyPath || import.meta.env?.VITE_ZKEY_PATH || 'public/turn_validator.zkey'

    consoleLogger.info(`Loading zKey file from: ${finalZKeyPath}`)

    // Load zKey file from public folder (browser-compatible)
    const zKey = await loadZKeyFromPath(finalZKeyPath)

    // Use snarkjs built-in curve functionality
    consoleLogger.info('Initializing BLS12-381 curve...')
    const curve = await getCurveFromName('bls12381')

    consoleLogger.info('Converting verification key points to uncompressed format...')
    const jsonPayload = await serializeVKeyPoints(zKey, curve)

    if (shouldDownload) {
      // Write/Download the JSON file
      const fileName = 'vkey_points.json'
      downloadFile(jsonPayload, fileName)
      consoleLogger.info(`✅ Success! Verification key points written to ${fileName} and downloaded!`)
    }

    // Also log the payload for debugging
    consoleLogger.info('Generated payload:', jsonPayload)

    // Return the JSON string so it can be used elsewhere
    return jsonPayload
  } catch (error) {
    consoleLogger.error('❌ Failed to generate verification key:', error)
    throw error
  }
}

/**
 * Browser-compatible function to export VKey points from a file input
 */
export async function exportVKeyPointsFromFile(file: File): Promise<void> {
  try {
    consoleLogger.info(`Loading zKey file from uploaded file: ${file.name}`)

    // Read file as Uint8Array
    const buffer = await file.arrayBuffer()
    const zKey = new Uint8Array(buffer)

    // Use snarkjs built-in curve functionality
    consoleLogger.info('Initializing BLS12-381 curve...')
    const curve = await getCurveFromName('bls12381')

    consoleLogger.info('Converting verification key points to uncompressed format...')
    const jsonPayload = await serializeVKeyPoints(zKey, curve)

    // Download the file
    downloadFile(jsonPayload, 'vkey_points.json')

    consoleLogger.info(`✅ Success! Verification key points exported and downloaded!`)
  } catch (error) {
    consoleLogger.error('❌ Failed to generate verification key:', error)
    throw error
  }
}

// async function main() {
//   try {
//     const zKeyPath = path.join(__dirname, '../../public/turn_validator.zkey')

//     consoleLogger.info('Exporting verification key...')
//     await exportVKeyPoints(zKeyPath)
//     consoleLogger.info('✅ vKey export completed successfully!')
//   } catch (err) {
//     consoleLogger.error('❌ Unhandled error in script:', err)
//     process.exit(1)
//   }
// }

// main().catch((err) => {
//   console.error('❌ Unhandled error in main():', err)
//   process.exit(1)
// })
