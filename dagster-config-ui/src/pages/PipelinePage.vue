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

    <div v-if="activeRunId" class="q-mt-md q-ml-xs row items-center q-gutter-sm">
      <q-badge :color="runStatusColor" text-color="white" class="q-px-sm q-py-xs">
        Run {{ activeRunId }}: {{ runStatus ?? 'UNKNOWN' }}
      </q-badge>
      <q-btn
        v-if="activeRunUrl"
        flat
        dense
        no-caps
        color="primary"
        icon="open_in_new"
        label="Open in Dagster"
        :href="activeRunUrl"
        target="_blank"
        rel="noopener noreferrer"
      />
      <q-spinner-dots
        v-if="isPollingStatus && !isTerminalStatus(runStatus)"
        color="primary"
        size="1.2em"
      />
    </div>
    <div v-if="statusError" class="text-negative q-mt-sm q-ml-xs">
      {{ statusError }}
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

import {computed, onBeforeUnmount, onMounted, ref} from 'vue';
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
const activeRunId = ref<string | null>(null);
const activeRunUrl = ref<string | null>(null);
const runStatus = ref<string | null>(null);
const statusError = ref<string | null>(null);
const isPollingStatus = ref(false);

const TERMINAL_STATUSES = new Set(["SUCCESS", "FAILURE", "CANCELED", "CANCELING"]);
const STATUS_POLL_INTERVAL_MS = 3000;
let statusPollTimer: ReturnType<typeof setInterval> | null = null;

const runStatusColor = computed(() => {
  if (runStatus.value === "SUCCESS") {
    return "positive";
  }
  if (runStatus.value === "FAILURE") {
    return "negative";
  }
  if (runStatus.value === "CANCELED" || runStatus.value === "CANCELING") {
    return "warning";
  }
  return "info";
});

onMounted(async () => {
  await getModules();
});

onBeforeUnmount(() => {
  stopStatusPolling();
});

const getModules = async () => {
  const res = await api.get(`pipelines/${route.params.pipelineName as string}/modules`);
  const raw = Array.isArray(res.data) ? res.data : [];
  moduleNames.value = raw
    .map(parseAssetName)
    .filter((v): v is AssetName => v !== null);
};

const isTerminalStatus = (status: string | null) => {
  return status !== null && TERMINAL_STATUSES.has(status);
};

const stopStatusPolling = () => {
  if (statusPollTimer !== null) {
    clearInterval(statusPollTimer);
    statusPollTimer = null;
  }
  isPollingStatus.value = false;
};

const fetchRunStatus = async () => {
  if (!activeRunId.value) {
    return;
  }

  try {
    isPollingStatus.value = true;
    const pipelineName = route.params.pipelineName as string;
    const response = await api.get(`/pipelines/${pipelineName}/runs/${activeRunId.value}/status`);
    const status = response.data?.status;
    const runUrl = response.data?.runUrl;

    runStatus.value = typeof status === "string" ? status : null;
    activeRunUrl.value = typeof runUrl === "string" && runUrl.length > 0 ? runUrl : activeRunUrl.value;
    statusError.value = null;

    if (isTerminalStatus(runStatus.value)) {
      stopStatusPolling();
    }
  } catch (error: unknown) {
    statusError.value = getApiErrorMessage(error, "Failed to refresh run status.");
    stopStatusPolling();
  } finally {
    if (statusPollTimer !== null) {
      isPollingStatus.value = false;
    }
  }
};

const startStatusPolling = () => {
  stopStatusPolling();
  void fetchRunStatus();
  statusPollTimer = setInterval(() => {
    void fetchRunStatus();
  }, STATUS_POLL_INTERVAL_MS);
};

const runPipeline = async () => {
  isLaunching.value = true;

  try {
    const pipelineName = route.params.pipelineName as string;
    const response = await api.post(`/pipelines/${pipelineName}/run`, {});
    const runId = response.data?.runId;
    const status = response.data?.status;
    const runUrl = response.data?.runUrl;

    const message = runId
      ? `Run started successfully (runId: ${runId}, status: ${status ?? 'UNKNOWN'})`
      : 'Run started successfully.';

    $q.notify({
      type: 'positive',
      message,
    });

    if (typeof runId === "string" && runId.length > 0) {
      activeRunId.value = runId;
      activeRunUrl.value = typeof runUrl === "string" && runUrl.length > 0 ? runUrl : null;
      runStatus.value = typeof status === "string" ? status : null;
      statusError.value = null;

      if (isTerminalStatus(runStatus.value)) {
        stopStatusPolling();
      } else {
        startStatusPolling();
      }
    }
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to start pipeline run.'),
    });
  } finally {
    isLaunching.value = false;
  }
};

</script>
