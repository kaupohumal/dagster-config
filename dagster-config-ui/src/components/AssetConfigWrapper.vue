<template>

  <!--  <q-select-->
  <!--    label="Select asset"-->
  <!--    v-model="selectedAsset"-->
  <!--    :options="assetOptions"-->
  <!--  />-->

  <q-card
    v-if="assetName === AssetName.Timeseries"
    class="q-pa-xs"
  >
    <HttpGetModuleConfig/>
  </q-card>

  <q-card
    v-if="assetName === AssetName.Mapper"
    class="q-pa-xs"
  >
    <JsonMapperConfig/>
  </q-card>

  <q-card
    v-if="assetName === AssetName.CsvWriter"
    class="q-pa-xs"
  >
    <CsvWriterConfig/>
  </q-card>

</template>

<script setup lang="ts">

import HttpGetModuleConfig from "components/HttpGetModuleConfig.vue";
import JsonMapperConfig from "components/JsonMapperConfig.vue";
import CsvWriterConfig from "components/CsvWriterConfig.vue";
import {AssetName, type AssetName as AssetNameType} from "components/models";

const assetName = defineModel<AssetNameType>('assetName', { required: true });

// const selectedAsset = ref<string|null>(null);
//
// const assetOptions = [
//   'Timeseries',
//   'Json Mapper',
//   'CSV Writer'
// ]

</script>
