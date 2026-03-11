<template>
  <div class="text-h6 q-mb-lg">http_get</div>
  <q-input
    label="URL"
    v-model="moduleEndpoint"
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
import {onMounted, ref} from 'vue';
import {api} from "boot/axios";
import {useRoute} from "vue-router";

const route = useRoute();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/http_get`;
const moduleEndpoint = ref<string|null>(null);
const eventType = ref<string|null>(null);
const pageSize = ref<number|null>(null);
const currentPage = ref<number|null>(null);

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  moduleEndpoint.value = res.data['endpoint'];
  eventType.value = res.data['eventType'];
  pageSize.value = res.data['pageSize'];
  currentPage.value = res.data['currentPage'];
}

const applyConfig = async () => {
  await api.patch(apiEndpoint, {
    'endpoint': moduleEndpoint.value,
    'eventType': eventType.value,
    'pageSize': pageSize.value,
    'currentPage': currentPage.value,
  });
}
//TODO: params based on source api type
</script>
