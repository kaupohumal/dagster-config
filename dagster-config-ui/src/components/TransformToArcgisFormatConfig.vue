<template>
  <div class="module-config">
    <div class="text-h6">transform_to_arcgis_format</div>
    <q-checkbox
      v-model="renameCoordinates"
      class="q-mt-sm"
    >
      <template #default>
        Rename latitude and longitude keys
        <q-icon
          name="help_outline"
          size="18px"
          color="grey-7"
          class="cursor-pointer q-ml-xs"
        >
          <q-tooltip>
            If the source data uses some other values than "lat" and "lng", add those values here.
          </q-tooltip>
        </q-icon>
      </template>
    </q-checkbox>
    <q-input
      v-if="renameCoordinates"
      label="Latitude field (lat)"
      v-model="lat"
    />
    <q-input
      v-if="renameCoordinates"
      class="q-mt-sm"
      label="Longitude field (lng)"
      v-model="lng"
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

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/transform_to_arcgis_format`;
const renameCoordinates = ref(false);
const lat = ref<string>('');
const lng = ref<string>('');

onMounted(async () => {
  await getModuleConfig();
});

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  lat.value = typeof res.data?.lat === 'string' ? res.data.lat : '';
  lng.value = typeof res.data?.lng === 'string' ? res.data.lng : '';
  renameCoordinates.value = lat.value.trim().length > 0 || lng.value.trim().length > 0;
};

const applyConfig = async () => {
  const normalizedLat = lat.value.trim();
  const normalizedLng = lng.value.trim();
  const payload: Record<string, string> = {};

  if (renameCoordinates.value) {
    if (normalizedLat.length > 0) {
      payload.lat = normalizedLat;
    }
    if (normalizedLng.length > 0) {
      payload.lng = normalizedLng;
    }
  }

  try {
    await api.patch(apiEndpoint, payload);

    $q.notify({
      type: 'positive',
      message: 'Saved transform_to_arcgis_format module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save transform_to_arcgis_format module changes.'),
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

