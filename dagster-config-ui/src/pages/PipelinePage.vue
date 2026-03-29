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

    <q-banner
      v-if="runMessage"
      class="q-mt-md"
      :class="runMessageIsError ? 'bg-red-1 text-red-10' : 'bg-green-1 text-green-10'"
    >
      {{ runMessage }}
    </q-banner>


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

const route = useRoute();
const moduleNames = ref<AssetName[]>([]);
const isLaunching = ref(false);
const runMessage = ref('');
const runMessageIsError = ref(false);

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
  runMessage.value = '';
  runMessageIsError.value = false;

  try {
    const pipelineName = route.params.pipelineName as string;
    const response = await api.post(`/pipelines/${pipelineName}/run`, {});
    const runId = response.data?.runId;
    const status = response.data?.status;

    runMessage.value = runId
      ? `Run started successfully (runId: ${runId}, status: ${status ?? 'UNKNOWN'})`
      : 'Run started successfully.';
  } catch (error: unknown) {
    const message = (error as { response?: { data?: { error?: string } } })?.response?.data?.error;
    runMessage.value = message || 'Failed to start pipeline run.';
    runMessageIsError.value = true;
  } finally {
    isLaunching.value = false;
  }
}

</script>
