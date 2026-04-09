<template>
  <q-page class="q-pa-xl">
    <div class="row items-center q-gutter-md">
      <div class="text-h5">Pipelines</div>
      <q-btn color="primary" label="Create pipeline" @click="openCreateDialog" />
    </div>

    <q-list class="q-mt-lg">
      <q-item
        v-for="(pipeline) in pipelines"
        :key="pipeline"
        clickable
        @click="router.push({ name: 'pipelineDetails', params: { pipelineName: pipeline } })"
      >
        <q-item-section>{{ pipeline }}</q-item-section>
      </q-item>
    </q-list>

    <q-dialog v-model="isCreateDialogOpen">
      <q-card style="min-width: 520px; max-width: 90vw">
        <q-card-section>
          <div class="text-h6">Create pipeline</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input v-model="pipelineName" label="Pipeline name" autofocus />

          <div class="text-subtitle2">Modules (ordered)</div>

          <div
            v-for="(moduleName, index) in moduleSelections"
            :key="`new-module-${moduleName}-${index}`"
            class="row items-center q-gutter-sm"
          >
            <q-select
              class="col"
              v-model="moduleSelections[index]"
              :options="moduleOptions"
              label="Module"
              emit-value
              map-options
            />
            <q-btn
              v-if="moduleSelections.length > 1"
              flat
              round
              icon="delete"
              color="negative"
              @click="removeModule(index)"
            />
          </div>

          <q-btn flat icon="add" label="Add module" @click="addModule" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="isCreateDialogOpen = false" />
          <q-btn
            color="primary"
            label="Create"
            :loading="isCreating"
            :disable="!canCreate"
            @click="createPipeline"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">

import { computed, onMounted, ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { ModuleCatalogEntry } from 'components/models';
import { getApiErrorMessage } from '../utils/errors';

const router = useRouter();
const $q = useQuasar();

const pipelines = ref<string[]>([]);
const moduleCatalog = ref<ModuleCatalogEntry[]>([]);
const isCreateDialogOpen = ref(false);
const isCreating = ref(false);
const pipelineName = ref('');
const moduleSelections = ref<string[]>([]);

const moduleOptions = computed(() =>
  moduleCatalog.value.map((entry) => ({
    label: `${entry.label} (${entry.module})`,
    value: entry.module,
  })),
);

const canCreate = computed(() => {
  if (isCreating.value) return false;
  if (!pipelineName.value.trim()) return false;
  if (moduleSelections.value.length === 0) return false;
  return moduleSelections.value.every((moduleName) => moduleName.trim().length > 0);
});

onMounted(async () => {
  await Promise.all([getPipelines(), getModuleCatalog()]);
  const firstModule = moduleCatalog.value.at(0)?.module;
  if (moduleSelections.value.length === 0 && firstModule) {
    moduleSelections.value = [firstModule];
  }
});

const getPipelines = async () => {
  const res = await api.get('/pipelines');
  pipelines.value = res.data;
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

const openCreateDialog = () => {
  pipelineName.value = '';
  const firstModule = moduleCatalog.value.at(0)?.module;
  moduleSelections.value = firstModule ? [firstModule] : [];
  isCreateDialogOpen.value = true;
};

const addModule = () => {
  const next = moduleCatalog.value[0]?.module;
  if (!next) return;
  moduleSelections.value.push(next);
};

const removeModule = (index: number) => {
  moduleSelections.value.splice(index, 1);
};

const createPipeline = async () => {
  isCreating.value = true;

  try {
    const normalizedName = pipelineName.value.trim();
    await api.post('/pipelines', {
      pipelineName: normalizedName,
      modules: moduleSelections.value,
    });

    $q.notify({
      type: 'positive',
      message: `Created pipeline '${normalizedName}'.`,
    });

    isCreateDialogOpen.value = false;
    await getPipelines();
    await router.push({ name: 'pipelineDetails', params: { pipelineName: normalizedName } });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to create pipeline.'),
    });
  } finally {
    isCreating.value = false;
  }
};


</script>
