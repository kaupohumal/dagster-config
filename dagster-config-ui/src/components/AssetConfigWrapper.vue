<template>
  <q-card flat bordered class="module-card">
    <q-card-section class="q-pa-sm module-card-title bg-grey-1">
      <div class="row items-center q-gutter-sm">
        <q-select
          dense
          outlined
          class="col"
          :model-value="props.selectedModule"
          :options="props.moduleOptions"
          :disable="props.isSwapping"
          emit-value
          map-options
          @update:model-value="onSwap"
        />
        <q-btn
          dense
          flat
          color="primary"
          icon="add"
          :disable="props.isAdding"
          @click="emit('add-after')"
        >
          <q-tooltip>Add module after this</q-tooltip>
        </q-btn>
        <q-btn
          dense
          flat
          color="negative"
          icon="delete"
          :loading="props.isRemoving"
          :disable="props.isRemoving"
          @click="emit('remove')"
        >
          <q-tooltip>Remove this module</q-tooltip>
        </q-btn>
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section class="q-pa-sm module-card-body">
      <HttpGetModuleConfig v-if="parsedAssetName === AssetName.Timeseries" :module-index="props.moduleIndex"/>
      <JsonMapperConfig v-else-if="parsedAssetName === AssetName.Mapper" :module-index="props.moduleIndex"/>
      <CsvWriterConfig v-else-if="parsedAssetName === AssetName.CsvWriter" :module-index="props.moduleIndex"/>
      <TransformToArcgisFormatConfig
        v-else-if="parsedAssetName === AssetName.TransformToArcgisFormat"
        :module-index="props.moduleIndex"
      />
      <SendToArcgisConfig v-else-if="parsedAssetName === AssetName.SendToArcgis" :module-index="props.moduleIndex"/>
      <template v-else>
        <div class="text-subtitle2">Unsupported module</div>
        <div class="text-caption text-grey-7">{{ props.assetName }}</div>
      </template>
    </q-card-section>
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
  moduleIndex: number;
  selectedModule: string;
  moduleOptions: Array<{ label: string; value: string }>;
  isSwapping: boolean;
  isRemoving: boolean;
  isAdding: boolean;
}>();

const emit = defineEmits<{
  swap: [value: unknown];
  'add-after': [];
  remove: [];
}>();

const parsedAssetName = computed(() => parseAssetName(props.assetName));

const onSwap = (value: unknown) => {
  emit('swap', value);
};

</script>

<style scoped>
.module-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.module-card-title {
  flex: 0 0 auto;
}

.module-card-body {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}

.module-card :deep(.module-config) {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
}

.module-card :deep(.module-save-btn) {
  margin-top: auto;
  align-self: flex-end;
}
</style>

