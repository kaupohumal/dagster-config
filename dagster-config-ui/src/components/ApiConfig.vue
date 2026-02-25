<template>

  <div class="text-h5 q-mb-lg">{{apiName}} Config</div>

  <q-input
    label="URL"
    v-model="apiUrl"
  />

  <div class="q-mt-lg">Params</div>
  <div
    v-for="(param, index) in params"
    :key="index"
    class="row q-gutter-x-xs"
  >
    <div class="col">
      <q-input
        label="Key"
        v-model="param.key"
      />
    </div>
    <div class="col">
      <q-input
        label="Value"
        v-model="param.value"
      />
    </div>
    <div class="col-1 flex content-center">
      <q-btn
        @click="params.splice(index, 1)"
        icon="close"
        color="negative"
        flat
      />
    </div>
  </div>
  <div class="col-1">
    <q-btn
      @click="params.push({key: '', value: ''})"
      icon="add"
      color="primary"
      class="q-mt-sm"
    />
  </div>
</template>

<script setup lang="ts">

import type {Parameter} from "components/models";
import {ref} from "vue";

const apiName = defineModel<string>('apiName');
const apiUrl = defineModel<string>("apiUrl", { default: "" });
const params = ref<Parameter[]>([{key: '', value: ''}]);

</script>
