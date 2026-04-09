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
      <template v-for="(moduleEntry, index) in moduleEntries" :key="`${moduleEntry.name}-${moduleEntry.index}`">
        <div
          class="pipeline-flow-item"
          :ref="setFlowItemRef"
        >
          <div class="row items-center q-gutter-sm q-mb-sm">
            <q-select
              dense
              outlined
              class="col"
              :model-value="moduleEntry.name"
              :options="moduleOptions"
              :disable="isSwappingByIndex[moduleEntry.index] === true"
              emit-value
              map-options
              @update:model-value="swapModule(moduleEntry.index, $event)"
            />
            <q-btn
              dense
              flat
              color="primary"
              icon="add"
              :disable="isAddingModule"
              @click="openAddModuleDialog(moduleEntry.index + 1)"
            >
              <q-tooltip>Add module after this</q-tooltip>
            </q-btn>
            <q-btn
              dense
              flat
              color="negative"
              icon="delete"
              :loading="isRemovingByIndex[moduleEntry.index] === true"
              :disable="isRemovingByIndex[moduleEntry.index] === true"
              @click="removeModule(moduleEntry.index)"
            >
              <q-tooltip>Remove this module</q-tooltip>
            </q-btn>
          </div>
          <AssetConfigWrapper
            :asset-name="moduleEntry.name"
            :module-index="moduleEntry.index"
          />
        </div>
        <div
          v-if="index < moduleEntries.length - 1"
          :key="`${moduleEntry.name}-${index}-arrow`"
          class="pipeline-flow-arrow"
          aria-hidden="true"
        >
          <q-icon name="east" size="20px"/>
        </div>
      </template>
    </div>

    <q-dialog v-model="isAddDialogOpen">
      <q-card style="min-width: 440px; max-width: 90vw">
        <q-card-section>
          <div class="text-h6">Add module</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <div class="text-caption text-grey-7">
            Insert at position {{ addInsertIndex }}
          </div>
          <q-select
            v-model="addTargetModule"
            :options="moduleOptions"
            emit-value
            map-options
            label="Module"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="isAddDialogOpen = false" />
          <q-btn
            color="primary"
            label="Add"
            :loading="isAddingModule"
            :disable="isAddingModule || !addTargetModule"
            @click="addModule"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">

import {computed, nextTick, onBeforeUnmount, onBeforeUpdate, onMounted, ref, watch, type ComponentPublicInstance} from 'vue';
import {api} from "boot/axios";
import AssetConfigWrapper from "components/AssetConfigWrapper.vue";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";
import type { ModuleCatalogEntry, ModuleEntry } from 'components/models';

const route = useRoute();
const $q = useQuasar();
const pipelineName = computed(() => route.params.pipelineName as string);
const moduleEntries = ref<ModuleEntry[]>([]);
const moduleCatalog = ref<ModuleCatalogEntry[]>([]);
const isSwappingByIndex = ref<Record<number, boolean>>({});
const isRemovingByIndex = ref<Record<number, boolean>>({});
const isAddDialogOpen = ref(false);
const isAddingModule = ref(false);
const addInsertIndex = ref(0);
const addTargetModule = ref('');
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

const moduleOptions = computed(() => moduleCatalog.value.map((entry) => ({
  label: `${entry.label} (${entry.module})`,
  value: entry.module,
})));

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
  await Promise.all([getModules(), getModuleCatalog()]);
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

watch(moduleEntries, async () => {
  await nextTick();
  observeCards();
  recomputeMaxCardHeight();
});

const getModules = async () => {
  const res = await api.get(`pipelines/${pipelineName.value}/module-entries`);
  const raw: unknown[] = Array.isArray(res.data) ? res.data : [];

  moduleEntries.value = raw.filter((entry: unknown): entry is ModuleEntry => {
    if (typeof entry !== 'object' || entry === null) {
      return false;
    }
    const typed = entry as { name?: unknown; index?: unknown };
    return typeof typed.name === 'string' && typeof typed.index === 'number';
  });
};

const getModuleCatalog = async () => {
  const res = await api.get('/module-catalog');
  const raw = Array.isArray(res.data) ? res.data : [];
  moduleCatalog.value = raw.filter(
    (entry: unknown): entry is ModuleCatalogEntry =>
      typeof entry === 'object'
      && entry !== null
      && typeof (entry as { module?: unknown }).module === 'string'
      && typeof (entry as { label?: unknown }).label === 'string'
      && typeof (entry as { default_asset?: unknown }).default_asset === 'string'
      && Array.isArray((entry as { required_resources?: unknown }).required_resources),
  );
};

const openAddModuleDialog = (insertIndex: number) => {
  addInsertIndex.value = insertIndex;
  addTargetModule.value = moduleCatalog.value.at(0)?.module ?? '';
  isAddDialogOpen.value = true;
};

const addModule = async () => {
  if (!addTargetModule.value) {
    return;
  }

  isAddingModule.value = true;
  try {
    await api.post(`/pipelines/${pipelineName.value}/assets`, {
      targetModule: addTargetModule.value,
      insertIndex: addInsertIndex.value,
    });

    $q.notify({
      type: 'positive',
      message: `Added '${addTargetModule.value}' at position ${addInsertIndex.value}.`,
    });

    isAddDialogOpen.value = false;
    await getModules();
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to add module.'),
    });
  } finally {
    isAddingModule.value = false;
  }
};

const removeModule = async (index: number) => {
  if (!window.confirm(`Remove module at position ${index}?`)) {
    return;
  }

  isRemovingByIndex.value[index] = true;
  try {
    await api.delete(`/pipelines/${pipelineName.value}/assets/${index}`);
    $q.notify({
      type: 'positive',
      message: `Removed module at position ${index}.`,
    });
    await getModules();
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to remove module.'),
    });
  } finally {
    isRemovingByIndex.value[index] = false;
  }
};

const swapModule = async (index: number, value: unknown) => {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return;
  }

  const targetModule = value.trim();
  const current = moduleEntries.value.find((entry) => entry.index === index)?.name;
  if (current === targetModule) {
    return;
  }

  if (!targetModule || targetModule.trim().length === 0) {
    return;
  }

  isSwappingByIndex.value[index] = true;

  try {
    const response = await api.patch(
      `/pipelines/${pipelineName.value}/assets/${index}/module`,
      {
        targetModule,
        preserveCompatibleParams: true,
        dryRun: false,
      },
    );

    const changed = Boolean(response.data?.changed);
    $q.notify({
      type: changed ? 'positive' : 'info',
      message: changed
        ? `Swapped asset ${index} to '${targetModule}'.`
        : `Asset ${index} already uses '${targetModule}'.`,
    });

    await getModules();
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to swap module.'),
    });
  } finally {
    isSwappingByIndex.value[index] = false;
  }
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
    const response = await api.get(`/pipelines/${pipelineName.value}/runs/${activeRunId.value}/status`);
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
    const response = await api.post(`/pipelines/${pipelineName.value}/run`, {});
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

