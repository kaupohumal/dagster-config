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
    <div class="pipeline-flow q-mt-lg q-ml-xs" :style="flowStyle">
      <template v-for="(moduleName, index) in moduleNames" :key="`${moduleName}-${index}`">
        <div
          class="pipeline-flow-item"
          :ref="setFlowItemRef"
        >
          <AssetConfigWrapper
            :asset-name="moduleName"
          />
        </div>
        <div
          v-if="index < moduleNames.length - 1"
          :key="`${moduleName}-${index}-arrow`"
          class="pipeline-flow-arrow"
          aria-hidden="true"
        >
          <q-icon name="east" size="20px"/>
        </div>
      </template>
    </div>

  </q-page>
</template>

<script setup lang="ts">

import {computed, nextTick, onBeforeUnmount, onBeforeUpdate, onMounted, ref, watch, type ComponentPublicInstance} from 'vue';
import {api} from "boot/axios";
import AssetConfigWrapper from "components/AssetConfigWrapper.vue";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();
const moduleNames = ref<string[]>([]);
const isLaunching = ref(false);
const activeRunId = ref<string | null>(null);
const activeRunUrl = ref<string | null>(null);
const runStatus = ref<string | null>(null);
const statusError = ref<string | null>(null);
const isPollingStatus = ref(false);
const flowItemRefs = ref<HTMLElement[]>([]);
const maxCardHeight = ref<number | null>(null);

const TERMINAL_STATUSES = new Set(["SUCCESS", "FAILURE", "CANCELED", "CANCELING"]);
const STATUS_POLL_INTERVAL_MS = 3000;
let statusPollTimer: ReturnType<typeof setInterval> | null = null;
let cardResizeObserver: ResizeObserver | null = null;

const flowStyle = computed(() => {
  if (maxCardHeight.value === null) {
    return {};
  }
  return {
    '--pipeline-card-max-height': `${maxCardHeight.value}px`,
  };
});

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
  await nextTick();
  observeCards();
  recomputeMaxCardHeight();
});

onBeforeUnmount(() => {
  stopStatusPolling();
  cardResizeObserver?.disconnect();
});

onBeforeUpdate(() => {
  flowItemRefs.value = [];
});

watch(moduleNames, async () => {
  await nextTick();
  observeCards();
  recomputeMaxCardHeight();
});

const getModules = async () => {
  const res = await api.get(`pipelines/${route.params.pipelineName as string}/modules`);
  const raw: unknown[] = Array.isArray(res.data)
    ? res.data
    : (Array.isArray(res.data?.modules) ? res.data.modules : []);

  moduleNames.value = raw
    .filter((v: unknown): v is string => typeof v === 'string' && v.trim().length > 0)
    .map((v: string) => v.trim());
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

const setFlowItemRef = (refEl: Element | ComponentPublicInstance | null) => {
  const el = refEl instanceof HTMLElement
    ? refEl
    : (refEl && '$el' in refEl && refEl.$el instanceof HTMLElement ? refEl.$el : null);

  if (el) {
    flowItemRefs.value.push(el);
  }
};

const recomputeMaxCardHeight = () => {
  let maxHeight = 0;

  for (const item of flowItemRefs.value) {
    const card = item.querySelector('.q-card');
    if (!(card instanceof HTMLElement)) {
      continue;
    }
    maxHeight = Math.max(maxHeight, Math.ceil(card.getBoundingClientRect().height));
  }

  maxCardHeight.value = maxHeight > 0 ? maxHeight : null;
};

const observeCards = () => {
  cardResizeObserver?.disconnect();

  if (typeof ResizeObserver === 'undefined') {
    return;
  }

  cardResizeObserver = new ResizeObserver(() => {
    recomputeMaxCardHeight();
  });

  for (const item of flowItemRefs.value) {
    const card = item.querySelector('.q-card');
    if (card instanceof HTMLElement) {
      cardResizeObserver.observe(card);
    }
  }
};

</script>

<style scoped>
.pipeline-flow {
  --pipeline-card-max-height: auto;
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 16px;
}

.pipeline-flow-item {
  flex: 1 1 340px;
  min-width: 320px;
  max-width: 460px;
}

.pipeline-flow-item :deep(.q-card) {
  min-height: var(--pipeline-card-max-height, auto);
  min-width: 0;
}

.pipeline-flow-item :deep(.text-h6) {
  overflow-wrap: anywhere;
}

.pipeline-flow-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: stretch;
  color: var(--q-primary);
  min-height: var(--pipeline-card-max-height, auto);
  width: 20px;
}

@media (max-width: 1023px) {
  .pipeline-flow-item {
    flex: 1 1 100%;
    min-width: 0;
    max-width: none;
  }

  .pipeline-flow-arrow {
    justify-content: center;
    margin-top: 10px;
  }
}
</style>

