//src/utils/general/parseData.ts

/**
 * Recursively converts string fields that contain only digits
 * into BigInt values inside a given object.
 *
 * @param obj - The input object whose string fields may be converted
 * @returns A new object with digit-only strings replaced by BigInt values
 */
export function convertStringFieldsToBigInt(obj: Record<string, unknown>): Record<string, unknown> {
  // Create a new object to store the results
  const result: Record<string, unknown> = {}

  // Iterate over all keys in the input object
  for (const key in obj) {
    // Case 1: If the value is a string that consists only of digits
    if (typeof obj[key] === 'string' && /^\d+$/.test(obj[key] as string)) {
      // Convert the string to BigInt and assign it to the result
      result[key] = BigInt(obj[key] as string)
      // Case 2: If the value is a non-null object (but not an array)
    } else if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
      // Recursively process this nested object
      result[key] = convertStringFieldsToBigInt(obj[key] as Record<string, unknown>)
      // Case 3: For all other types (numbers, arrays, booleans, etc.)
    } else {
      result[key] = obj[key] // Keep the value unchanged
    }
  }
  // Return the new object with applied conversions
  return result
}
