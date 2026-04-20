<template>
  <div class="module-config">
    <q-input
      label="URL"
      v-model="moduleEndpoint"
    />
    <q-select
      class="q-mt-sm"
      label="Authentication"
      v-model="authType"
      :options="authTypeOptions"
      emit-value
      map-options
    />
    <template v-if="authType === 'api_key'">
      <q-input
        class="q-mt-sm"
        label="API key"
        v-model="apiKey"
      />
      <q-input
        class="q-mt-sm"
        label="API key name"
        v-model="apiKeyName"
      />
    </template>
    <template v-else-if="authType === 'basic_auth'">
      <q-input
        class="q-mt-sm"
        label="Username"
        v-model="basicUsername"
      />
      <q-input
        class="q-mt-sm"
        type="password"
        label="Password"
        v-model="basicPassword"
      />
    </template>
    <template v-else-if="authType === 'bearer_token'">
      <q-input
        class="q-mt-sm"
        type="password"
        label="Bearer token"
        v-model="bearerToken"
      />
    </template>
    <div class="q-mt-lg">Params</div>
    <div
      v-for="(param, index) in params"
      :key="index"
      class="pair-row"
    >
      <div class="pair-field">
        <q-input
          label="Key"
          v-model="param.key"
        />
      </div>
      <div class="pair-field">
        <q-input
          label="Value"
          v-model="param.value"
        />
      </div>
      <div class="pair-action">
        <q-btn
          @click="params.splice(index, 1)"
          icon="close"
          color="negative"
          dense
          flat
        />
      </div>
    </div>
    <div>
      <q-btn
        @click="params.push(createEmptyPair(PARAMETER_FIELDS))"
        icon="add"
        color="primary"
        class="q-mt-sm"
      />
    </div>
    <q-btn
      @click="applyConfig"
      label="Save"
      class="module-save-btn"
      color="primary"
    />
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue';
import {api} from "boot/axios";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {
  createEmptyPair,
  type HttpAuthPayload,
  type HttpAuthType,
  normalizePairList,
  PARAMETER_FIELDS,
  type Parameter,
} from "components/models";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();
const props = defineProps<{
  moduleIndex: number;
}>();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/http_get/${props.moduleIndex}`;
const moduleEndpoint = ref<string|null>(null);
const params = ref<Parameter[]>([createEmptyPair(PARAMETER_FIELDS)]);
const authTypeOptions: Array<{label: string; value: HttpAuthType}> = [
  {label: 'No auth', value: 'none'},
  {label: 'API key', value: 'api_key'},
  {label: 'Basic auth', value: 'basic_auth'},
  {label: 'Bearer token', value: 'bearer_token'},
];
const authType = ref<HttpAuthType>('none');
const apiKey = ref<string>('');
const apiKeyName = ref<string>('');
const basicUsername = ref<string>('');
const basicPassword = ref<string>('');
const bearerToken = ref<string>('');

const clearAuthFields = () => {
  apiKey.value = '';
  apiKeyName.value = '';
  basicUsername.value = '';
  basicPassword.value = '';
  bearerToken.value = '';
};

const normalizeAuthType = (rawAuth: unknown): HttpAuthType => {
  if (typeof rawAuth !== 'object' || rawAuth === null) {
    clearAuthFields();
    return 'none';
  }

  const auth = rawAuth as Record<string, unknown>;
  if (typeof auth.api_key === 'object' && auth.api_key !== null) {
    const apiKeyAuth = auth.api_key as Record<string, unknown>;
    apiKey.value = typeof apiKeyAuth.key === 'string' ? apiKeyAuth.key : '';
    apiKeyName.value = typeof apiKeyAuth.key_name === 'string' ? apiKeyAuth.key_name : '';
    basicUsername.value = '';
    basicPassword.value = '';
    bearerToken.value = '';
    return 'api_key';
  }
  if (typeof auth.basic_auth === 'object' && auth.basic_auth !== null) {
    const basicAuth = auth.basic_auth as Record<string, unknown>;
    basicUsername.value = typeof basicAuth.username === 'string' ? basicAuth.username : '';
    basicPassword.value = typeof basicAuth.password === 'string' ? basicAuth.password : '';
    apiKey.value = '';
    apiKeyName.value = '';
    bearerToken.value = '';
    return 'basic_auth';
  }
  if (typeof auth.bearer_token === 'object' && auth.bearer_token !== null) {
    const bearerAuth = auth.bearer_token as Record<string, unknown>;
    bearerToken.value = typeof bearerAuth.token === 'string' ? bearerAuth.token : '';
    apiKey.value = '';
    apiKeyName.value = '';
    basicUsername.value = '';
    basicPassword.value = '';
    return 'bearer_token';
  }

  clearAuthFields();
  return 'none';
};

const buildAuthPayload = (): HttpAuthPayload => {
  if (authType.value === 'api_key') {
    return {
      api_key: {
        key: apiKey.value,
        key_name: apiKeyName.value,
      },
    };
  }

  if (authType.value === 'basic_auth') {
    return {
      basic_auth: {
        username: basicUsername.value,
        password: basicPassword.value,
      },
    };
  }

  if (authType.value === 'bearer_token') {
    return {
      bearer_token: {
        token: bearerToken.value,
      },
    };
  }

  return {};
};

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  moduleEndpoint.value = res.data['endpoint'];
  params.value = normalizePairList(res.data?.params, PARAMETER_FIELDS);
  authType.value = normalizeAuthType(res.data?.auth);
}

const applyConfig = async () => {
  try {
    await api.patch(apiEndpoint, {
      'endpoint': moduleEndpoint.value,
      'params': params.value,
      'auth': buildAuthPayload(),
    });

    $q.notify({
      type: 'positive',
      message: 'Saved http_get module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save http_get module changes.'),
    });
  }
}
</script>

<style scoped>
.module-config {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
}

.pair-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 8px;
}

.pair-field {
  flex: 1 1 0;
  min-width: 0;
}

.pair-action {
  flex: 0 0 auto;
  padding-top: 10px;
}

.module-save-btn {
  margin-top: auto;
  align-self: flex-end;
}
</style>

