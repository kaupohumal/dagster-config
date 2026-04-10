<template>
  <div class="module-config">
    <div class="text-caption q-mb-sm">
      MinIO secret key: <strong>{{ minioSecretKeySet ? 'Set' : 'Not set' }}</strong>
    </div>
    <q-input
      class="q-mb-sm"
      label="MinIO host"
      v-model="minioHost"
    />
    <q-input
      class="q-mb-sm"
      label="MinIO access key"
      v-model="minioAccessKey"
    />
    <q-input
      class="q-mb-sm"
      type="password"
      label="New MinIO secret key"
      hint="Leave empty to keep the current secret key"
      v-model="minioSecretKey"
    />
    <q-btn
      flat
      color="warning"
      label="Clear stored secret key"
      class="self-start q-mb-md"
      @click="clearSecretKey"
    />
    <q-input
      class="q-mt-md"
      label="MinIO bucket"
      v-model="minioBucket"
    />
    <q-input
      label="File name"
      v-model="fileName"
    />
    <q-btn
      @click="applyConfig"
      label="Save"
      class="module-save-btn"
      color="primary"
    />
  </div>
</template>

<script setup lang="ts">

import {onMounted, ref} from "vue";
import {api} from "boot/axios";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();
const props = defineProps<{
  moduleIndex: number;
}>();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/write_to_csv/${props.moduleIndex}`;
const fileName = ref<string>('bus_validations.csv')
const minioHost = ref<string>('');
const minioAccessKey = ref<string>('');
const minioBucket = ref<string>('dagster-integration');
const minioSecretKey = ref<string>('');
const minioSecretKeySet = ref<boolean>(false);

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  fileName.value = typeof res.data?.fileName === 'string' ? res.data.fileName : '';
  minioHost.value = typeof res.data?.minioHost === 'string' ? res.data.minioHost : '';
  minioAccessKey.value = typeof res.data?.minioAccessKey === 'string' ? res.data.minioAccessKey : '';
  minioBucket.value = typeof res.data?.minioBucket === 'string' ? res.data.minioBucket : '';
  minioSecretKeySet.value = Boolean(res.data?.minioSecretKeySet);
}

const applyConfig = async () => {
  try {
    const payload: Record<string, unknown> = {
      fileName: fileName.value,
      minioHost: minioHost.value,
      minioAccessKey: minioAccessKey.value,
      minioBucket: minioBucket.value,
    };

    if (minioSecretKey.value.trim().length > 0) {
      payload.minioSecretKey = minioSecretKey.value;
    }

    await api.patch(apiEndpoint, payload);

    minioSecretKey.value = '';
    await getModuleConfig();

    $q.notify({
      type: 'positive',
      message: 'Saved write_to_csv module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save write_to_csv module changes.'),
    });
  }
}

const clearSecretKey = async () => {
  try {
    await api.patch(apiEndpoint, {
      minioSecretKey: '',
    });

    minioSecretKey.value = '';
    minioSecretKeySet.value = false;
    $q.notify({
      type: 'positive',
      message: 'Cleared MinIO secret key.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to clear MinIO secret key.'),
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

.module-save-btn {
  margin-top: auto;
  align-self: flex-end;
}
</style>

