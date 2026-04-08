<template>
  <q-card
    v-if="parsedAssetName === AssetName.Timeseries"
    class="q-pa-xs module-card"
  >
    <HttpGetModuleConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.Mapper"
    class="q-pa-xs module-card"
  >
    <JsonMapperConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.CsvWriter"
    class="q-pa-xs module-card"
  >
    <CsvWriterConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.TransformToArcgisFormat"
    class="q-pa-xs module-card"
  >
    <TransformToArcgisFormatConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.SendToArcgis"
    class="q-pa-xs module-card"
  >
    <SendToArcgisConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === null"
    class="q-pa-md"
  >
    <div class="text-subtitle2">Unsupported module</div>
    <div class="text-caption text-grey-7">{{ props.assetName }}</div>
  </q-card>

</template>

<script setup lang="ts">

import {computed} from "vue";

import HttpGetModuleConfig from "components/HttpGetModuleConfig.vue";
import JsonMapperConfig from "components/JsonMapperConfig.vue";
import CsvWriterConfig from "components/CsvWriterConfig.vue";
import TransformToArcgisFormatConfig from "components/TransformToArcgisFormatConfig.vue";
import SendToArcgisConfig from "components/SendToArcgisConfig.vue";
import {AssetName, parseAssetName} from "components/models";

const props = defineProps<{
  assetName: string;
}>();

const parsedAssetName = computed(() => parseAssetName(props.assetName));

</script>

<style scoped>
.module-card {
  display: flex;
  flex-direction: column;
}

.module-card :deep(.module-config) {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 100%;
}

.module-card :deep(.module-save-btn) {
  margin-top: auto;
  align-self: flex-end;
}
</style>

