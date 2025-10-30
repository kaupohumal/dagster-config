<template>
  <q-page class="row items-center justify-evenly">

    <q-select
      v-model="selectedUnits"
      :options="unitOptions"
      label="Units"
    />


    <q-btn
      label="Set Units"
      @click="setUnits(selectedUnits)"
    />

  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { api } from 'boot/axios';

const unitOptions = ref<string[]>([
  'metric',
  'imperial',
  'standard'
]);

const selectedUnits = ref<string>('metric');

const setUnits = async (units: string) => {
  const res = await api.post('/units', { 'units': units });
  console.log(res);
}

</script>
