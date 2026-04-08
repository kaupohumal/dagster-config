<template>
  <div class="module-config">
    <div class="text-h6">write_to_csv</div>
    <q-input
      label="File name"
      v-model="fileName"
    />
    <q-btn
      @click="applyConfig"
      label="Save"
      class="module-save-btn"
      color="primary"
    />
  </div>
</template>

<script setup lang="ts">

import {onMounted, ref} from "vue";
import {api} from "boot/axios";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/write_to_csv`;
const fileName = ref<string>('bus_validations.csv')

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  fileName.value = res.data['fileName'];
}

const applyConfig = async () => {
  try {
    await api.patch(apiEndpoint, {
      'fileName': fileName.value
    });

    $q.notify({
      type: 'positive',
      message: 'Saved write_to_csv module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save write_to_csv module changes.'),
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

.module-save-btn {
  margin-top: auto;
  align-self: flex-end;
}
</style>

