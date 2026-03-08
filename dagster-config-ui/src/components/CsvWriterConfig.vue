<template>

  <div class="text-h6">write_to_csv</div>
  <q-input
    label="File name"
    v-model="fileName"
  />
  <q-btn
    @click="applyConfig"
    label="Save"
    class="q-mt-md"
    color="primary"
  />
</template>

<script setup lang="ts">

import {ref} from "vue";
import {api} from "boot/axios";
import {useRoute} from "vue-router";

const route = useRoute();

const fileName = ref<string>('bus_validations.csv')

const applyConfig = async () => {
  await api.patch(`pipelines/${route.params.pipelineName as string}/modules/write_to_csv`, {
    'fileName': fileName.value
  });
}
</script>
