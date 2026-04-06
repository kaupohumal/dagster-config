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
        v-model="mapping.value"
      />
    </div>
    <div class="col">
      <q-input
        label="Target"
        v-model="mapping.key"
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
      @click="mappings.push(createEmptyPair(MAPPING_FIELDS))"
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
import {
  createEmptyPair,
  MAPPING_FIELDS,
  normalizePairList,
  type Mapping,
} from "components/models";
import {api} from "boot/axios";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/json_mapper`;
const mappings = ref<Mapping[]>([createEmptyPair(MAPPING_FIELDS)]);

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  mappings.value = normalizePairList(res.data?.mappings, MAPPING_FIELDS);
}

const applyConfig = async () => {
  try {
    await api.patch(apiEndpoint, {
      'mappings': mappings.value,
    });

    $q.notify({
      type: 'positive',
      message: 'Saved json_mapper module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save json_mapper module changes.'),
    });
  }
}

</script>
