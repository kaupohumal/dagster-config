<template>
  <div class="module-config">
    <div class="text-caption q-mb-sm">
      ArcGIS token: <strong>{{ tokenSet ? 'Set' : 'Not set' }}</strong>
    </div>
    <q-input
      class="q-mb-sm"
      type="password"
      label="New ArcGIS token"
      hint="Leave empty to keep the current token"
      v-model="arcgisToken"
    />
    <q-btn
      flat
      color="warning"
      label="Clear stored token"
      class="self-start q-mb-md"
      @click="clearToken"
    />
    <q-input
      class="q-mt-sm"
      label="Feature service address"
      v-model="featureServiceAddress"
    />
    <q-input
      label="Layer name"
      v-model="layerName"
    />
    <q-input
      class="q-mt-sm"
      label="Sublayer name"
      v-model="sublayerName"
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

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/send_to_arcgis/${props.moduleIndex}`;
const layerName = ref<string>('');
const sublayerName = ref<string>('');
const featureServiceAddress = ref<string>('');
const arcgisToken = ref<string>('');
const tokenSet = ref<boolean>(false);

onMounted(async () => {
  await getModuleConfig();
});

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  layerName.value = typeof res.data?.layerName === 'string' ? res.data.layerName : '';
  sublayerName.value = typeof res.data?.sublayerName === 'string' ? res.data.sublayerName : '';
  featureServiceAddress.value = typeof res.data?.featureServiceAddress === 'string'
    ? res.data.featureServiceAddress
    : '';
  tokenSet.value = Boolean(res.data?.tokenSet);
};

const applyConfig = async () => {
  try {
    const payload: Record<string, unknown> = {
      layerName: layerName.value,
      sublayerName: sublayerName.value,
      featureServiceAddress: featureServiceAddress.value,
    };

    if (arcgisToken.value.trim().length > 0) {
      payload.arcgisToken = arcgisToken.value;
    }

    await api.patch(apiEndpoint, payload);
    arcgisToken.value = '';
    await getModuleConfig();

    $q.notify({
      type: 'positive',
      message: 'Saved send_to_arcgis module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save send_to_arcgis module changes.'),
    });
  }
};

const clearToken = async () => {
  try {
    await api.patch(apiEndpoint, {
      arcgisToken: '',
    });

    tokenSet.value = false;
    $q.notify({
      type: 'positive',
      message: 'Cleared ArcGIS token.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to clear ArcGIS token.'),
    });
  }
};

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

