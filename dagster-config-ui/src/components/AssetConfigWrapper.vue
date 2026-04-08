<template>
  <q-card
    v-if="parsedAssetName === AssetName.Timeseries"
    class="q-pa-xs"
  >
    <HttpGetModuleConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.Mapper"
    class="q-pa-xs"
  >
    <JsonMapperConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.CsvWriter"
    class="q-pa-xs"
  >
    <CsvWriterConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.TransformToArcgisFormat"
    class="q-pa-xs"
  >
    <TransformToArcgisFormatConfig/>
  </q-card>

  <q-card
    v-if="parsedAssetName === AssetName.SendToArcgis"
    class="q-pa-xs"
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
