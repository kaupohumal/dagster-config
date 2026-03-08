<template>
  <q-page class="q-pa-xl">

    <div class="text-h4">Pipeline: {{route.params.pipelineName}}</div>


    <div class="text-h5 q-mt-xl q-ml-xs">Modules:</div>
    <div class="row q-gutter-x-md q-mt-lg q-ml-xs">
      <div
        class="col"
        v-for="moduleName in moduleNames"
        :key="moduleName"
      >
        <AssetConfigWrapper
          :assetName="moduleName"
        />
      </div>

    </div>

  </q-page>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';
import {api} from "boot/axios";
import AssetConfigWrapper from "components/AssetConfigWrapper.vue";
import {useRoute} from "vue-router";
import {parseAssetName, type AssetName} from "components/models";

const route = useRoute();
const moduleNames = ref<AssetName[]>([]);

onMounted(async () => {
  await getModules();
})

const getModules = async () => {
  const res = await api.get(`pipelines/${route.params.pipelineName as string}/modules`);
  const raw = Array.isArray(res.data) ? res.data : [];
  moduleNames.value = raw
    .map(parseAssetName)
    .filter((v): v is AssetName => v !== null);
}

</script>
