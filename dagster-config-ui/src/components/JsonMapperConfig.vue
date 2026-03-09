<template>
  <div class="text-h6">json_mapper</div>
  <div
    v-for="(mapping, index) in mappings"
    :key="index"
    class="row q-gutter-x-lg"
  >
    <div class="col">
      <q-input
        label="Source"
        v-model="mapping.source"
      />
    </div>
    <div class="col">
      <q-input
        label="Target"
        v-model="mapping.target"
      />
    </div>
    <div class="col-1 flex content-center">
      <q-btn
        @click="mappings.splice(index, 1)"
        icon="close"
        color="negative"
        flat
      />
    </div>
  </div>
  <div class="col-1">
    <q-btn
      @click="mappings.push({source: '', target: ''})"
      icon="add"
      color="primary"
      class="q-mt-sm"
    />
  </div>
  <q-btn
    @click="applyConfig"
    label="Save"
    class="q-mt-md"
    color="primary"
  />
</template>

<script setup lang="ts">

import {onMounted, ref} from "vue";
import type {Mapping} from "components/models";
import {api} from "boot/axios";
import {useRoute} from "vue-router";

const route = useRoute();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/json_mapper`;
const mappings = ref<Mapping[]>([]);

onMounted(async () => {
  await getModuleConfig()
})

const normalizeMappings = (raw: unknown): Mapping[] => {
  if (!Array.isArray(raw)) return [{ source: '', target: '' }];

  const normalized: Mapping[] = raw
    .filter((m): m is Record<string, unknown> => typeof m === 'object' && m !== null)
    .map((m) => ({
      source: typeof m.source === 'string' ? m.source : '',
      target: typeof m.target === 'string' ? m.target : '',
    }));

  return normalized.length > 0 ? normalized : [{ source: '', target: '' }];
}

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  mappings.value = normalizeMappings(res.data?.mappings);
}

const applyConfig = async () => {
  await api.patch(apiEndpoint, {
    'mappings': mappings.value,
  });
}

</script>
