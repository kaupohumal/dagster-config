<template>
  <q-page class="q-pa-xl">

    <div class="row items-center q-gutter-md">
      <div class="text-h4">Pipeline: {{ route.params.pipelineName }}</div>
      <q-btn
        color="primary"
        label="Run pipeline"
        :loading="isLaunching"
        :disable="isLaunching"
        @click="runPipeline"
      />
    </div>

    <div class="text-h5 q-mt-xl q-ml-xs">Modules:</div>
    <div class="row q-gutter-x-md q-mt-lg q-ml-xs">
      <div
        class="col"
        v-for="moduleName in moduleNames"
        :key="moduleName"
      >
        <AssetConfigWrapper
          :assetName="moduleName"
        />
      </div>

    </div>

  </q-page>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';
import {api} from "boot/axios";
import AssetConfigWrapper from "components/AssetConfigWrapper.vue";
import {useRoute} from "vue-router";
import {parseAssetName, type AssetName} from "components/models";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();
const moduleNames = ref<AssetName[]>([]);
const isLaunching = ref(false);

onMounted(async () => {
  await getModules();
})

const getModules = async () => {
  const res = await api.get(`pipelines/${route.params.pipelineName as string}/modules`);
  const raw = Array.isArray(res.data) ? res.data : [];
  moduleNames.value = raw
    .map(parseAssetName)
    .filter((v): v is AssetName => v !== null);
}

const runPipeline = async () => {
  isLaunching.value = true;

  try {
    const pipelineName = route.params.pipelineName as string;
    const response = await api.post(`/pipelines/${pipelineName}/run`, {});
    const runId = response.data?.runId;
    const status = response.data?.status;

    const message = runId
      ? `Run started successfully (runId: ${runId}, status: ${status ?? 'UNKNOWN'})`
      : 'Run started successfully.';

    $q.notify({
      type: 'positive',
      message,
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to start pipeline run.'),
    });
  } finally {
    isLaunching.value = false;
  }
}

</script>
