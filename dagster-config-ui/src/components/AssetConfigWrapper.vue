<template>

  <!--  <q-select-->
  <!--    label="Select asset"-->
  <!--    v-model="selectedAsset"-->
  <!--    :options="assetOptions"-->
  <!--  />-->

  <div
    v-if="assetName === AssetName.Timeseries"
    class="q-mt-xl"
  >
    <SmartCityApiConfig/>
  </div>

  <div
    v-if="assetName === AssetName.Mapper"
    class="q-mt-xl"
  >
    <JsonMapperConfig/>
  </div>

  <div
    v-if="assetName === AssetName.CsvWriter"
    class="q-mt-xl"
  >
    <CsvWriterConfig/>
  </div>

</template>

<script setup lang="ts">

import SmartCityApiConfig from "components/SmartCityApiConfig.vue";
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
