/* eslint-disable @typescript-eslint/no-explicit-any */
declare module 'ffjavascript' {
  export const Scalar: {
    e(value: string | number, radix?: number): any
    eq(a: any, b: any): boolean
    toString(value: any): string
  }

  export function buildBn128(singleThread?: boolean): Promise<any>
  export function buildBls12381(singleThread?: boolean): Promise<any>
}
