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

export interface ModuleCatalogEntry {
  module: AssetName;
  label: string;
  default_asset: string;
  default_params: Record<string, unknown>;
  required_resources: string[];
}

export interface ModuleEntry {
  name: string;
  asset: string | null;
  ins: string | string[] | Record<string, unknown> | null;
  index: number;
}

export interface CreatePipelinePayload {
  pipelineName: string;
  modules: Array<string | { module: string; params?: Record<string, unknown> }>;
  jobName?: string;
}

export interface CopyPipelinePayload {
  targetPipelineName: string;
}

export interface PipelineSchedule {
  hasSchedule: boolean;
  cron: string | null;
}

export interface SwapModulePayload {
  targetModule: string;
  preserveCompatibleParams?: boolean;
}

export type HttpAuthType = 'none' | 'api_key' | 'basic_auth' | 'bearer_token';

export interface HttpApiKeyAuth {
  key?: string;
  key_name: string;
}

export interface HttpBasicAuth {
  username: string;
  password?: string;
}

export interface HttpBearerTokenAuth {
  token?: string;
}

export interface HttpAuthPayload {
  api_key?: HttpApiKeyAuth;
  basic_auth?: HttpBasicAuth;
  bearer_token?: HttpBearerTokenAuth;
}

export interface HttpApiKeyAuthResponse {
  key_name: string;
  keySet: boolean;
}

export interface HttpBasicAuthResponse {
  username: string;
  passwordSet: boolean;
}

export interface HttpBearerTokenAuthResponse {
  tokenSet: boolean;
}

export interface HttpAuthResponse {
  api_key?: HttpApiKeyAuthResponse;
  basic_auth?: HttpBasicAuthResponse;
  bearer_token?: HttpBearerTokenAuthResponse;
}

export interface HttpPaginationPayload {
  currentPageParameterName: string;
  responseDataPath: string;
}

export type HttpPaginationResponse = HttpPaginationPayload;

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
  TransformToArcgisFormat: 'transform_to_arcgis_format',
  SendToArcgis: 'send_to_arcgis',
} as const;

export type AssetName = (typeof AssetName)[keyof typeof AssetName];

export const assetNameOptions: AssetName[] = [
  AssetName.Timeseries,
  AssetName.Mapper,
  AssetName.CsvWriter,
  AssetName.TransformToArcgisFormat,
  AssetName.SendToArcgis,
];

function normalizeAssetName(value: unknown): string | null {
  if (typeof value !== 'string') return null;

  const withoutControlChars = Array.from(value)
    .filter((char) => {
      const code = char.charCodeAt(0);
      return !(code <= 31 || code === 127);
    })
    .join('');

  const normalized = value
    .trim()
    .replace(/^['"]+|['"]+$/g, '')
    .toLowerCase()
    .replace(/-/g, '_')
    .replace(/\s+/g, '');
  const cleaned = withoutControlChars
    .trim()
    .replace(/^['"]+|['"]+$/g, '')
    .toLowerCase()
    .replace(/-/g, '_')
    .replace(/\s+/g, '');

  return cleaned.length > 0 ? cleaned : (normalized.length > 0 ? normalized : null);
}

export function isAssetName(value: unknown): value is AssetName {
  const normalized = normalizeAssetName(value);
  if (!normalized) return false;

  return (assetNameOptions as readonly string[]).includes(normalized);
}

export function parseAssetName(value: unknown): AssetName | null {
  const normalized = normalizeAssetName(value);
  if (!normalized) return null;

  if ((assetNameOptions as readonly string[]).includes(normalized)) {
    return normalized as AssetName;
  }

  return null;
}
