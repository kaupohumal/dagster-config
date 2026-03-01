<template>
  <div class="text-h6 q-mb-lg">Timeseries-db1 API Config</div>
  <q-input
    label="URL"
    v-model="timeseriesApiEndpoint"
  />
  <div class="q-mt-lg text-bold">Params
    <q-input
      label="Event type"
      v-model="eventType"
    />
    <q-input
      label="Page size"
      v-model="pageSize"
      type="number"
    />
    <q-input
      label="Current page"
      v-model="currentPage"
      type="number"
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
import {ref} from 'vue';
import {api} from "boot/axios";

const timeseriesApiEndpoint = ref<string>('https://timeseries-db1.cloud.ut.ee/event');
const eventType = ref<string>('ridango_validations');
const pageSize = ref<number>(50);
const currentPage = ref<number>(1);

const applyConfig = async () => {
  await api.patch('/assets/http_get', { //TODO: fix endpoint naming
    'timeseriesApiEndpoint': timeseriesApiEndpoint.value,
    'eventType': eventType.value,
    'pageSize': pageSize.value,
    'currentPage': currentPage.value,
  });
}

//TODO: read current data from api
</script>
