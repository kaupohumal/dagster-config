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
      <div class="text-caption q-mb-sm">
        API key: <strong>{{ apiKeySet ? 'Set' : 'Not set' }}</strong>
      </div>
      <q-input
        class="q-mt-sm"
        type="password"
        label="New API key"
        hint="Leave empty to keep the current API key"
        v-model="apiKey"
      />
      <q-btn
        flat
        color="warning"
        label="Clear stored API key"
        class="self-start q-mb-md"
        @click="clearSecret"
      />
      <q-input
        class="q-mt-md"
        label="API key name"
        v-model="apiKeyName"
      />
    </template>
    <template v-else-if="authType === 'basic_auth'">
      <div class="text-caption q-mb-sm">
        Password: <strong>{{ basicPasswordSet ? 'Set' : 'Not set' }}</strong>
      </div>
      <q-input
        class="q-mt-sm"
        label="Username"
        v-model="basicUsername"
      />
      <q-input
        class="q-mt-sm"
        type="password"
        label="New password"
        hint="Leave empty to keep the current password"
        v-model="basicPassword"
      />
      <q-btn
        flat
        color="warning"
        label="Clear stored password"
        class="self-start q-mb-md"
        @click="clearSecret"
      />
    </template>
    <template v-else-if="authType === 'bearer_token'">
      <div class="text-caption q-mb-sm">
        Bearer token: <strong>{{ bearerTokenSet ? 'Set' : 'Not set' }}</strong>
      </div>
      <q-input
        class="q-mt-sm"
        type="password"
        label="New bearer token"
        hint="Leave empty to keep the current token"
        v-model="bearerToken"
      />
      <q-btn
        flat
        color="warning"
        label="Clear stored token"
        class="self-start q-mb-md"
        @click="clearSecret"
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
  type HttpAuthResponse,
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
const apiKeySet = ref<boolean>(false);
const basicPasswordSet = ref<boolean>(false);
const bearerTokenSet = ref<boolean>(false);

const clearAuthFields = () => {
  apiKey.value = '';
  apiKeyName.value = '';
  basicUsername.value = '';
  basicPassword.value = '';
  bearerToken.value = '';
};

const clearSecretFlags = () => {
  apiKeySet.value = false;
  basicPasswordSet.value = false;
  bearerTokenSet.value = false;
};

const normalizeAuthType = (rawAuth: unknown): HttpAuthType => {
  if (typeof rawAuth !== 'object' || rawAuth === null) {
    clearAuthFields();
    clearSecretFlags();
    return 'none';
  }

  const auth = rawAuth as HttpAuthResponse;
  if (typeof auth.api_key === 'object' && auth.api_key !== null) {
    apiKeyName.value = typeof auth.api_key.key_name === 'string' ? auth.api_key.key_name : '';
    apiKeySet.value = Boolean(auth.api_key.keySet);
    basicUsername.value = '';
    basicPassword.value = '';
    bearerToken.value = '';
    basicPasswordSet.value = false;
    bearerTokenSet.value = false;
    apiKey.value = '';
    return 'api_key';
  }

  if (typeof auth.basic_auth === 'object' && auth.basic_auth !== null) {
    basicUsername.value = typeof auth.basic_auth.username === 'string' ? auth.basic_auth.username : '';
    basicPasswordSet.value = Boolean(auth.basic_auth.passwordSet);
    apiKey.value = '';
    apiKeyName.value = '';
    basicPassword.value = '';
    bearerToken.value = '';
    apiKeySet.value = false;
    bearerTokenSet.value = false;
    return 'basic_auth';
  }

  if (typeof auth.bearer_token === 'object' && auth.bearer_token !== null) {
    bearerTokenSet.value = Boolean(auth.bearer_token.tokenSet);
    apiKey.value = '';
    apiKeyName.value = '';
    basicUsername.value = '';
    basicPassword.value = '';
    bearerToken.value = '';
    apiKeySet.value = false;
    basicPasswordSet.value = false;
    return 'bearer_token';
  }

  clearAuthFields();
  clearSecretFlags();
  return 'none';
};

const buildAuthPayload = (): HttpAuthPayload => {
  if (authType.value === 'api_key') {
    if (apiKey.value.trim().length > 0) {
      return {
        api_key: {
          key_name: apiKeyName.value,
          key: apiKey.value,
        },
      };
    }
    return {
      api_key: {
        key_name: apiKeyName.value,
      },
    };
  }

  if (authType.value === 'basic_auth') {
    if (basicPassword.value.trim().length > 0) {
      return {
        basic_auth: {
          username: basicUsername.value,
          password: basicPassword.value,
        },
      };
    }
    return {
      basic_auth: {
        username: basicUsername.value,
      },
    };
  }

  if (authType.value === 'bearer_token') {
    if (bearerToken.value.trim().length > 0) {
      return {
        bearer_token: {
          token: bearerToken.value,
        },
      };
    }
    return {
      bearer_token: {},
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

    clearAuthFields();
    await getModuleConfig();

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

const clearSecret = async () => {
  try {
    let authPayload: HttpAuthPayload = {};

    if (authType.value === 'api_key') {
      authPayload = {
        api_key: {
          key_name: apiKeyName.value,
          key: '',
        },
      };
    } else if (authType.value === 'basic_auth') {
      authPayload = {
        basic_auth: {
          username: basicUsername.value,
          password: '',
        },
      };
    } else if (authType.value === 'bearer_token') {
      authPayload = {
        bearer_token: {
          token: '',
        },
      };
    }

    await api.patch(apiEndpoint, {auth: authPayload});
    clearAuthFields();
    await getModuleConfig();

    $q.notify({
      type: 'positive',
      message: 'Cleared stored auth secret.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to clear auth secret.'),
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

