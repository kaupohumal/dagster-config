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

import {ref} from "vue";
import type {Mapping} from "components/models";
import {api} from "boot/axios";
import {useRoute} from "vue-router";

const route = useRoute();

const mappings = ref<Mapping[]>([{source: 'events[*].device_identity', target: 'device_identity'}]);

const applyConfig = async () => {
  await api.patch(`pipelines/${route.params.pipelineName as string}/modules/json_mapper`, {
    'mappings': mappings.value,
  });
}

</script>
