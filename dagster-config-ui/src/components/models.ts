export interface Parameter {
  key: string;
  value: string;
}

export interface Mapping {
  target: string;
  source: string;
}

export const AssetName = {
  Timeseries: 'http_get',
  Mapper: 'json_mapper',
  CsvWriter: 'write_to_csv',
} as const;

export type AssetName = (typeof AssetName)[keyof typeof AssetName];

export const assetNameOptions: AssetName[] = [
  AssetName.Timeseries,
  AssetName.Mapper,
  AssetName.CsvWriter,
];

export function isAssetName(value: unknown): value is AssetName {
  return typeof value === 'string' && (assetNameOptions as readonly string[]).includes(value);
}

export function parseAssetName(value: unknown): AssetName | null {
  return isAssetName(value) ? value : null;
}
