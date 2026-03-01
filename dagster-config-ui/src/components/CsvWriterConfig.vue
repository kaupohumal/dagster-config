<template>

  <div class="text-h6">CSV Writer Config</div>
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

const fileName = ref<string>('bus_validations.csv')

const applyConfig = async () => {
  await api.patch('/assets/write_to_csv', {
    'fileName': fileName.value
  });
}
</script>
