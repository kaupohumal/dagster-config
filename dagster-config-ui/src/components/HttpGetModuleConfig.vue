<template>
  <div class="module-config">
    <div class="text-h6 q-mb-lg">http_get</div>
    <q-input
      label="URL"
      v-model="moduleEndpoint"
    />
    <div class="q-mt-lg">Params</div>
    <div
      v-for="(param, index) in params"
      :key="index"
      class="pair-row"
    >
      <div class="pair-field">
        <q-input
          label="Key"
          v-model="param.key"
        />
      </div>
      <div class="pair-field">
        <q-input
          label="Value"
          v-model="param.value"
        />
      </div>
      <div class="pair-action">
        <q-btn
          @click="params.splice(index, 1)"
          icon="close"
          color="negative"
          dense
          flat
        />
      </div>
    </div>
    <div>
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
      class="module-save-btn"
      color="primary"
    />
  </div>
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

<style scoped>
.module-config {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
}

.pair-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 8px;
}

.pair-field {
  flex: 1 1 0;
  min-width: 0;
}

.pair-action {
  flex: 0 0 auto;
  padding-top: 10px;
}

.module-save-btn {
  margin-top: auto;
  align-self: flex-end;
}
</style>

