export type StringPair<K extends string, V extends string> = Record<K | V, string>;

export interface PairFieldNames<K extends string, V extends string> {
  key: K;
  value: V;
}

export const KEY_VALUE_FIELDS = {
  key: 'key',
  value: 'value',
} as const;

export const PARAMETER_FIELDS = KEY_VALUE_FIELDS;
export const MAPPING_FIELDS = KEY_VALUE_FIELDS;

export type Parameter = StringPair<typeof PARAMETER_FIELDS.key, typeof PARAMETER_FIELDS.value>;
export type Mapping = StringPair<typeof MAPPING_FIELDS.key, typeof MAPPING_FIELDS.value>;

export function createEmptyPair<K extends string, V extends string>(
  fields: PairFieldNames<K, V>,
): StringPair<K, V> {
  return {
    [fields.key]: '',
    [fields.value]: '',
  } as StringPair<K, V>;
}

export function normalizePairList<K extends string, V extends string>(
  raw: unknown,
  fields: PairFieldNames<K, V>,
): StringPair<K, V>[] {
  if (!Array.isArray(raw)) return [createEmptyPair(fields)];

  const normalized: StringPair<K, V>[] = raw
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((item) => ({
      [fields.key]: typeof item[fields.key] === 'string' ? item[fields.key] : '',
      [fields.value]: typeof item[fields.value] === 'string' ? item[fields.value] : '',
    }) as StringPair<K, V>);

  return normalized.length > 0 ? normalized : [createEmptyPair(fields)];
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
