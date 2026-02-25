<template>
  <q-page class="q-pa-xl">
    <div class="row q-gutter-x-xl">

      <div class="col">
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
      </div>

      <div class="col">
        <div class="text-h6">Mappings</div>
        <div
          v-for="(mapping, index) in mappings"
          :key="index"
          class="row q-gutter-x-lg"
        >
          <div class="col">
            <q-input
              label="Source"
              v-model="mapping.source"
            />
          </div>
          <div class="col">
            <q-input
              label="Target"
              v-model="mapping.target"
            />
          </div>
          <div class="col-1 flex content-center">
            <q-btn
              @click="mappings.splice(index, 1)"
              icon="close"
              color="negative"
              flat
            />
          </div>
        </div>
        <div class="col-1">
          <q-btn
            @click="mappings.push({source: '', target: ''})"
            icon="add"
            color="primary"
            class="q-mt-sm"
          />
        </div>
      </div>

      <div class="col">
        <div class="text-h6">Write to CSV Config</div>
        <q-input
          label="File name"
          v-model="fileName"
        />
      </div>

    </div>

    <div class="row q-mt-xl">
      <q-btn
        @click="applyConfig"
      >Save Configurations
      </q-btn>
    </div>


  </q-page>
</template>

<script setup lang="ts">

import {ref} from 'vue';
import {api} from "boot/axios";
import type {Mapping} from "components/models";

const timeseriesApiEndpoint = ref<string>('https://timeseries-db1.cloud.ut.ee/event');
const eventType = ref<string>('ridango_validations');
const pageSize = ref<number>(50);
const currentPage = ref<number>(1);
const mappings = ref<Mapping[]>([{source: 'events[*].device_identity', target: 'device_identity'}]);
const fileName = ref<string>('bus_validations.csv')

const applyConfig = async () => {
  const res = await api.post('/config', {
    'timeseriesApiEndpoint': timeseriesApiEndpoint.value,
    'eventType': eventType.value,
    'pageSize': pageSize.value,
    'currentPage': currentPage.value,
    'mappings': mappings.value,
    'fileName': fileName.value
  });
  console.log(res);
}

</script>
