<template>
  <q-page class="q-pa-xl">
    <div class="row q-gutter-x-xl">

      <div class="col">
        <ApiConfig
          :apiName="'Source'"
          v-model:apiUrl="sourceApiUrl"
        />
      </div>

      <div class="col">
        <div class="row">Mappings</div>
        <div class="row">
        </div>
        <q-input
          label="Mapping"
          v-model="sourceUrl"

        />
      </div>

      <div class="col">
        <ApiConfig
          :apiName="'Target'"
        />
      </div>
    </div>

    <div class="row q-mt-xl">
      <q-btn
        @click="applyConfig"
      >Save Configurations</q-btn>
    </div>


  </q-page>
</template>

<script setup lang="ts">

import {ref} from 'vue';
import ApiConfig from "components/ApiConfig.vue";
import {api} from "boot/axios";

const sourceUrl = ref<string>('');
const sourceApiUrl = ref<string>('');

const applyConfig = async () => {
  console.log(sourceApiUrl.value);
  const res = await api.post('/config', {
    'sourceApiUrl': sourceApiUrl.value
  });
  console.log(res);
}

</script>
