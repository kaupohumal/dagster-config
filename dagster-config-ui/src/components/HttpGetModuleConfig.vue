<template>
  <div class="text-h6 q-mb-lg">http_get</div>
  <q-input
    label="URL"
    v-model="moduleEndpoint"
  />
  <div class="q-mt-lg">Params</div>
  <div
    v-for="(param, index) in params"
    :key="index"
    class="row q-gutter-x-xs"
  >
    <div class="col">
      <q-input
        label="Key"
        v-model="param.key"
      />
    </div>
    <div class="col">
      <q-input
        label="Value"
        v-model="param.value"
      />
    </div>
    <div class="col-1 flex content-center">
      <q-btn
        @click="params.splice(index, 1)"
        icon="close"
        color="negative"
        flat
      />
    </div>
  </div>
  <div class="col-1">
    <q-btn
      @click="params.push(createEmptyPair(PARAMETER_FIELDS))"
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
import {onMounted, ref} from 'vue';
import {api} from "boot/axios";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {
  createEmptyPair,
  normalizePairList,
  PARAMETER_FIELDS,
  type Parameter,
} from "components/models";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/http_get`;
const moduleEndpoint = ref<string|null>(null);
const params = ref<Parameter[]>([createEmptyPair(PARAMETER_FIELDS)]);

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  moduleEndpoint.value = res.data['endpoint'];
  params.value = normalizePairList(res.data?.params, PARAMETER_FIELDS);
}

const applyConfig = async () => {
  try {
    await api.patch(apiEndpoint, {
      'endpoint': moduleEndpoint.value,
      'params': params.value,
    });

    $q.notify({
      type: 'positive',
      message: 'Saved http_get module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save http_get module changes.'),
    });
  }
}
</script>
