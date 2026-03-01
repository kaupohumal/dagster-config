<template>
  <q-page class="q-pa-xl">

    <div class="text-h5">Pipelines</div>
    <q-list
      class="q-mt-lg"
    >
      <q-item
        v-for="(pipeline) in pipelines"
        :key="pipeline"
        clickable
        @click="router.push('pipelines/' + pipeline)"
      >
        {{ pipeline }}
      </q-item>
    </q-list>

  </q-page>
</template>

<script setup lang="ts">

import {onMounted, ref} from "vue";
import {api} from "boot/axios";
import {useRouter} from "vue-router";

const router = useRouter();

const pipelines = ref<string[]>([]);

onMounted(async () => {
  await getPipelines();
})

const getPipelines = async () => {
  const res = await api.get('/pipelines');
  console.log(res);
  pipelines.value = res.data;
}


</script>
