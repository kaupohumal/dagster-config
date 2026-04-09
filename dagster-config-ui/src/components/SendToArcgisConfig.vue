<template>
  <div class="module-config">
    <div class="text-h6">send_to_arcgis</div>
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
};

const applyConfig = async () => {
  try {
    await api.patch(apiEndpoint, {
      layerName: layerName.value,
      sublayerName: sublayerName.value,
      featureServiceAddress: featureServiceAddress.value,
    });

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

