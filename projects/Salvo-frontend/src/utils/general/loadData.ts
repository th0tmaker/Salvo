//src/utils/general/loadData.ts

/**
 * Loads a `.zkey` binary file from a given path/URL
 * and returns its contents as a Uint8Array.
 *
 * @param path - The URL or local path to the zKey file
 * @returns A Promise resolving to a Uint8Array of the file's binary contents
 */
export async function loadZKeyFromPath(path: string): Promise<Uint8Array> {
  // Try block
  try {
    // Fetch the file from the given path (works with URLs or relative paths in a browser environment)
    const response = await fetch(path)
    // Throw error if response was not successful
    if (!response.ok) {
      throw new Error(`Failed to fetch ${path}: ${response.status} ${response.statusText}`)
    }
    // Convert the response into an ArrayBuffer (raw binary data)
    const buffer = await response.arrayBuffer()
    // Wrap the ArrayBuffer into a Uint8Array
    return new Uint8Array(buffer)
    // Catch error if method fails
  } catch (error) {
    throw new Error(`Failed to load zKey file from ${path}: ${error}`)
  }
}

/**
 * Loads a JSON file from a given path/URL
 * and returns its parsed contents as a typed object.
 *
 * @param path - The URL or local path to the JSON file
 * @returns A Promise resolving to the parsed JSON object of type T
 */
export async function loadJSONFromPath<T>(path: string): Promise<T> {
  try {
    // Fetch the file from the given path (works with URLs or relative paths in a browser environment)
    const response = await fetch(path)

    // Throw an error if the HTTP response was not successful
    if (!response.ok) {
      throw new Error(`Failed to fetch ${path}: ${response.status} ${response.statusText}`)
    }

    // Read the response body as text
    const text = await response.text()

    // Parse the JSON text into an object of type T
    return JSON.parse(text) as T
  } catch (error) {
    // Catch any errors and wrap them in a descriptive message
    throw new Error(`Failed to load JSON file from ${path}: ${error}`)
  }
}
